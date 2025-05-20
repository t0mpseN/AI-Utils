# vector_store.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import numpy as np

def create_vector_store(documents, persist_directory="vector_store"):
    # More reliable embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Verify documents have content
    valid_docs = [doc for doc in documents if doc.page_content.strip()]
    if not valid_docs:
        raise ValueError("No valid documents with content found!")
    
    # Create store with validation
    try:
        vector_store = Chroma.from_documents(
            documents=valid_docs,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        print(f"✅ Vector store created with {len(valid_docs)} documents")
        return vector_store
    except Exception as e:
        print("⚠️ Error creating vector store. Testing embeddings...")
        _test_embeddings(embeddings, valid_docs[0].page_content)
        raise

def _test_embeddings(embeddings, sample_text):
    """Verify embeddings are generated correctly"""
    try:
        emb = embeddings.embed_query(sample_text)
        print(f"Embedding test successful (dim={len(emb)})")
    except Exception as e:
        print(f"Embedding failed: {str(e)}")
        print("Sample text:", sample_text[:100])