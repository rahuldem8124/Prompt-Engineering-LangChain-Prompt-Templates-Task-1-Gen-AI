import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    has_llm = True
except ImportError:
    has_llm = False

class GraphState(TypedDict):
    question: str
    documents: List[str]
    intent: str
    generation: str
    escalation_required: bool

class CustomerSupportBot:
    def __init__(self, db_path="./chroma_db"):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
        
        # Use a dummy LLM response if real one isn't available
        # In a real scenario, use ChatGoogleGenerativeAI, ChatOpenAI, etc.
        self.llm = self._setup_llm()

    def _setup_llm(self):
        if has_llm and os.environ.get("GOOGLE_API_KEY"):
            return ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
        return None
        
    def intent_router(self, state: GraphState) -> GraphState:
        print("--- INTENT ROUTER ---")
        question = state.get("question", "").lower()
        # Dummy Intent logic: escalate if the word "angry" or "human" is present
        if "angry" in question or "human" in question or "manager" in question:
            print("=> Intent: Escalation requested.")
            return {"escalation_required": True, "intent": "escalation"}
        print("=> Intent: Standard QA.")
        return {"escalation_required": False, "intent": "qa"}

    def retrieve(self, state: GraphState) -> GraphState:
        print("--- RETRIEVAL ---")
        question = state["question"]
        docs = self.retriever.invoke(question)
        doc_texts = [d.page_content for d in docs]
        print(f"=> Retrieved {len(doc_texts)} chunks.")
        return {"documents": doc_texts}

    def generate(self, state: GraphState) -> GraphState:
        print("--- GENERATION ---")
        question = state["question"]
        docs = state.get("documents", [])
        context = "\n\n".join(docs)
        
        if self.llm:
            prompt = f"You are a helpful customer support bot. Answer the question based on the context.\nContext: {context}\nQuestion: {question}"
            response = self.llm.invoke([HumanMessage(content=prompt)])
            gen = response.content
        else:
            gen = f"[DUMMY LLM] Answer based on context: {context[:100]}..."

        print("=> Answer Generated.")
        return {"generation": gen}

    def hitl_node(self, state: GraphState) -> GraphState:
        print("--- HUMAN IN THE LOOP (PENDING) ---")
        print(f"System halted. Administrator review required for query: {state['question']}")
        # When execution hits here, the checkpointer preserves the state.
        # This node is registered with interrupt_before, so it won't actually run until resumed.
        return state

def should_escalate(state: GraphState):
    if state["escalation_required"]:
        return "escalate"
    return "retrieve"

def create_workflow():
    bot = CustomerSupportBot()
    
    workflow = StateGraph(GraphState)
    
    workflow.add_node("intent_router", bot.intent_router)
    workflow.add_node("retrieve", bot.retrieve)
    workflow.add_node("generate", bot.generate)
    workflow.add_node("hitl_node", bot.hitl_node)

    workflow.add_edge(START, "intent_router")
    
    workflow.add_conditional_edges(
        "intent_router",
        should_escalate,
        {
            "escalate": "hitl_node",
            "retrieve": "retrieve"
        }
    )
    
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    # After HITL intervention, the human could direct it to generate or end.
    workflow.add_edge("hitl_node", END)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["hitl_node"])
    return app

if __name__ == "__main__":
    app = create_workflow()
    config = {"configurable": {"thread_id": "1"}}
    
    print("\n--- TEST CASE 1: STANDARD QA ---")
    inputs = {"question": "What is the return policy?"}
    for event in app.stream(inputs, config, stream_mode="values"):
        pass
    final_state = app.get_state(config).values
    print("Final Output:", final_state.get("generation"))
    
    print("\n--- TEST CASE 2: HITL ESCALATION ---")
    config2 = {"configurable": {"thread_id": "2"}}
    inputs2 = {"question": "I am angry, let me talk to a human!"}
    for event in app.stream(inputs2, config2, stream_mode="values"):
        pass
    
    # Check if workflow was interrupted
    state2 = app.get_state(config2)
    next_node = state2.next
    if "hitl_node" in next_node:
        print("SUCCESS: Execution correctly halted and awaits Human-In-The-Loop.")
    else:
        print("FAILED: Did not route to HITL.")
