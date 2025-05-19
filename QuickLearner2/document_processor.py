import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader

# In document_processor.py, modify the load_documents function:
def load_documents(directory_path):
    directory_path = os.path.normpath(directory_path)  # Convert to OS-specific path
    if not os.path.exists(directory_path):
        raise ValueError(f"Document directory does not exist: {directory_path}")
    
    loader = DirectoryLoader(
        directory_path,
        glob="**/*.*",
        loader_cls=lambda path: TextLoader(path) if path.endswith('.txt') else PyPDFLoader(path)
    )
    return loader.load()

def split_documents(documents):
    # Split documents into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return text_splitter.split_documents(documents)