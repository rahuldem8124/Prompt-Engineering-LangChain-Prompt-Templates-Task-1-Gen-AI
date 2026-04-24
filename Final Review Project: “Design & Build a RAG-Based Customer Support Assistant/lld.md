# Low-Level Design (LLD): RAG-Based Customer Support Assistant

## 1. Module-Level Design

### Document Processing & Chunking Module
- **Purpose**: Intake raw PDFs and prepare them for embedding.
- **Components**: `PyPDFLoader` to read the document. `RecursiveCharacterTextSplitter` configured with `chunk_size=1000` and `chunk_overlap=150` characters. This ensures boundaries overlap enough to not abruptly cut sentences.

### Embedding & Vector Storage Module
- **Purpose**: Generates vector representations and stores them persistently.
- **Components**: Sentences are routed through an embedding model (e.g., `SentenceTransformer` or `OpenAIEmbeddings`), yielding lists of floats. These are inserted into a ChromaDB persistent client pointing to a local directory `./chroma_db`.

### Retrieval & Query Processing Module
- **Purpose**: Retrieve nearest neighbors for a given text.
- **Components**: Exposed via a `.similarity_search(query, k=4)` interface. 

### Graph Execution & HITL Module
- **Purpose**: Managing workflow states and pausing execution when required.
- **Components**: Constructed using `langgraph.graph.StateGraph`. Implements a shared `dict` state between nodes. `MemorySaver` sqlite checkpointer is used to persist state and allow for graph interruptions (HITL).

## 2. Data Structures

**Document Representation**
```json
{
  "page_content": "Extracted text payload...",
  "metadata": {"source": "manual.pdf", "page": 5}
}
```

**State Object for LangGraph**
```python
from typing import TypedDict, List
class WorkflowState(TypedDict):
    question: str
    documents: List[str]
    intent: str
    generation: str
    escalation_required: bool
    human_feedback: str
```

## 3. Workflow Design (LangGraph)

- **Nodes**:
  - `intent_router`: Receives user input and populates `state["intent"]`. Checks rules for escalation.
  - `retrieve`: If intent is standard QA, fetches Chunks from ChromaDB and populates `state["documents"]`.
  - `generate`: Synthesizes final response based on `state["question"]` and `state["documents"]`.
  - `human_approval`: A node designed to pause execution securely using LangGraph's interruption framework.

- **Edges**:
  - `START -> intent_router`
  - Conditional Edge from `intent_router`:
    - If `escalation_required == True` -> `human_approval`
    - Else -> `retrieve`
  - `retrieve -> generate`
  - `human_approval -> generate` (or returns directly to user).
  - `generate -> END`

## 4. Conditional Routing Logic

The routing node incorporates the following logic:
1. **Answer Generation Criteria**: If the query is an informational extraction mapped to standard business domains (e.g., "what is the return policy"), `escalation_required` is set to `False`.
2. **Escalation Criteria**: If the query contains trigger words (e.g., "angry", "lawyer", "manager"), or if the retriever's similarity score is below a predefined confidence limit, the intent parser flags `escalation_required = True`.

## 5. HITL Design

- **Trigger**: The LangGraph compilation includes `interrupt_before=["human_approval"]`. The workflow halts right before the human node executes.
- **Escalation Action**: An asynchronous notification alerts an agent UI. The graph state remains dormant in the Memory Checkpointer database.
- **Resolution**: An administrator reviews the `state["question"]`, optionally provides `state["human_feedback"]`, and issues a resume command (`app.invoke(None, thread_config)`).

## 6. API / Interface Design 

**Input Format (Invoke Workflow):**
```json
{
  "input": {"question": "I need help with my refund."},
  "config": {"configurable": {"thread_id": "user_123"}}
}
```

**Output Format:**
```json
{
  "generation": "To process your refund, please follow these steps...",
  "status": "completed"
}
```

## 7. Error Handling

- **Missing Data**: If parsing fails or the database is missing, the system gracefully degrades by immediately triggering HITL and noting "System Error: KB Unavailable."
- **No Relevant Chunks Found**: If retrieval returns an empty list or extremely low-relevance scores, `generate` node returns a canned response ("I couldn't find exact information on that, let me connect you to an agent.") and sets `escalation_required`.
- **LLM Failure**: Generation API timeout or rate-limits are caught via typical `try/except` blocks, executing a backoff retry up to 3 times before returning a fallback response.
