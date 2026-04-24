import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from src.loader import load_pdf
from src.chunker import chunk_documents
from src.embeddings import load_or_create_vectorstore

def ingest_pdf(pdf_path: str, persist_directory: str = "./chroma_db"):
    try:
        documents = load_pdf(pdf_path)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    chunks = chunk_documents(documents)
    load_or_create_vectorstore(chunks=chunks, persist_directory=persist_directory)

if __name__ == "__main__":
    pdf_file = "knowledge_base.pdf"
    if not os.path.exists(pdf_file):
        print(f"File {pdf_file} not found. Please run create_pdf.py first.")
    else:
        ingest_pdf(pdf_file)
