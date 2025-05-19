# quicklearner/__init__.py
from .document_processor import load_documents, split_documents
from .vector_store import create_vector_store
from .ollama_integration import setup_llm
from .rag_pipeline import create_rag_pipeline
from .main import QuickLearner

__all__ = ['load_documents', 'split_documents', 'create_vector_store', 
           'setup_llm', 'create_rag_pipeline', 'QuickLearner']