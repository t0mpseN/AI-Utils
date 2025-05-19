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
    """Split universal para qualquer tipo de documento"""
    text_splitter = RecursiveCharacterTextSplitter(
        # Configurações balanceadas para a maioria dos documentos
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\n\n",  # Quebras de parágrafo
            "\n",     # Quebras de linha
            " ",      # Espaços
            "",       # Último recurso
        ],
        keep_separator=True,
        is_separator_regex=False
    )
    
    return text_splitter.split_documents(documents)