# vector_store.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def create_vector_store(documents, persist_directory="vector_store"):
    # Use a valid sentence-transformers model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",  # Correct model name or try embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        model_kwargs={'device': 'cpu'}  # Use 'cuda' if you have GPU
    )
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    return vector_store