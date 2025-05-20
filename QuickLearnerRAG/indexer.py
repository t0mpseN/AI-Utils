#indexer.py
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

def index_pdf(document_path):
    # Carrega o PDF
    loader = PyPDFLoader(document_path)  # Altere para o nome do seu arquivo
    pages = loader.load()

    # Divide o texto em pedaços menores
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(pages)

    # Cria embeddings com modelo local do Ollama
    embedding = OllamaEmbeddings(model="nomic-embed-text")

    # Cria o índice FAISS a partir dos documentos
    db = FAISS.from_documents(docs, embedding)

    # Salva localmente
    db.save_local("banco_documento")

    print("✅ PDF indexado com sucesso!")
