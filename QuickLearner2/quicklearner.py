# quicklearner.py
import os
from pathlib import Path
from document_processor import load_documents, split_documents
from vector_store import create_vector_store
from ollama_integration import setup_llm
from rag_pipeline import create_rag_pipeline

class QuickLearner:
    def __init__(self, document_directory, model_name="steamdj/llama3.1-cpu-only:latest"):
        # Convert to absolute path
        doc_path = Path(document_directory)
        if not doc_path.is_absolute():
            doc_path = Path(__file__).parent / document_directory
        
        if not doc_path.exists():
            raise ValueError(f"Document directory not found at: {doc_path}")
        
        # Load and process documents
        documents = load_documents(str(doc_path))
        split_docs = split_documents(documents)
        
        # Create vector store
        self.vector_store = create_vector_store(split_docs)
        
        # Setup LLM and RAG pipeline
        self.llm = setup_llm(model_name)
        self.qa_pipeline = create_rag_pipeline(self.llm, self.vector_store)
    
    def query(self, question):
        # Get answer with source documents
        result = self.qa_pipeline.invoke({"query": question})
        return {
            "answer": result["result"],
            "sources": [doc.metadata for doc in result["source_documents"]]
        }