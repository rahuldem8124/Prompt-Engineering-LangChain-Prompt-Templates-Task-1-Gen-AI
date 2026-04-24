from src.rag_pipeline import build_rag_pipeline, generate_answer
import os

def main():
    pdf_path = input("Enter the path to your PDF file (or press Enter to use default 'knowledge_base.pdf'): ").strip()
    # Remove quotes if user pastes path from "Copy as path" in Windows
    pdf_path = pdf_path.strip('"').strip("'")
    
    if not pdf_path:
        pdf_path = "knowledge_base.pdf"

    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return
        
    print(f"\nProcessing '{pdf_path}'...")
    vectorstore = build_rag_pipeline(pdf_path)

    while True:
        query = input("\nAsk a question (or type 'exit'): ")

        if query.lower() == "exit":
            break

        try:
            answer = generate_answer(vectorstore, query)
            print("\nAnswer:\n", answer)
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
