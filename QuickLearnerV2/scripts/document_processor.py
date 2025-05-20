import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader

import logging
from pdfminer.high_level import extract_text
from langchain.schema import Document
from typing import List

# Silence PDFMiner warnings
logging.getLogger('pdfminer').setLevel(logging.ERROR)

def load_documents(directory_path: str) -> List[Document]:
    """Robust document loader with proper encoding handling"""
    directory_path = os.path.normpath(directory_path)
    
    if os.path.isdir(directory_path):
        return load_directory(directory_path)
    elif os.path.isfile(directory_path):
        return load_single_file(directory_path)
    else:
        raise ValueError(f"Path does not exist: {directory_path}")

def load_directory(directory_path: str) -> List[Document]:
    """Load all PDFs from directory with error handling"""
    documents = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf'):
            filepath = os.path.join(directory_path, filename)
            try:
                documents.extend(load_single_file(filepath))
            except Exception as e:
                print(f"⚠️ Error loading {filename}: {str(e)}")
                continue
    return documents

# document_processor.py
def load_single_file(filepath: str) -> List[Document]:
    """Robust PDF loading with proper error handling"""
    try:
        # Simple text extraction without layout params
        text = extract_text(filepath)
        pages = text.split('\x0c')  # Split by form feed
        
        return [
            Document(
                page_content=page.strip(),
                metadata={
                    "source": filepath,
                    "page": i,
                    "total_pages": len(pages)
                }
            )
            for i, page in enumerate(pages)
            if page.strip()
        ]
    except Exception as e:
        print(f"⚠️ Fallback: Trying alternative PDF reader for {filepath}")
        return _load_with_pypdf(filepath)  # Fallback method

def _load_with_pypdf(filepath: str) -> List[Document]:
    """Fallback loader using pypdf"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return [
            Document(
                page_content=page.extract_text() or "",  # Handle None
                metadata={
                    "source": filepath,
                    "page": i,
                    "total_pages": len(reader.pages)
                }
            )
            for i, page in enumerate(reader.pages)
        ]
    except Exception as e:
        raise ValueError(f"Failed to load {filepath} with all methods: {str(e)}")

'''def load_documents(directory_path):
    directory_path = os.path.normpath(directory_path)  # Convert to OS-specific path
    if not os.path.exists(directory_path):
        raise ValueError(f"Document directory does not exist: {directory_path}")
    
    loader = DirectoryLoader(
        directory_path,
        glob="**/*.*",
        loader_cls=lambda path: TextLoader(path) if path.endswith('.txt') else PyPDFLoader(path)
    )
    return loader.load()'''

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