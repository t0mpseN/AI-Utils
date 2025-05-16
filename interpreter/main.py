import os
import sys
import io
import pychm
import requests
import fitz  # PyMuPDF
import shutil
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import Chroma

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === Configuration ===
SOURCE = "RevitAPI.chm"  # Change to PDF path or URL
CHROMA_DB_DIR = "./chroma_db"
MODEL_NAME = "gemma3"

shutil.rmtree(CHROMA_DB_DIR, ignore_errors=True)

# === Helper Functions ===
def load_pdf(path):
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    return text

def load_html(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()


def load_chm(chm_path):
    """Extract text from CHM using PyCHM (best if available)."""
    try:
        chm = pychm.CHMFile()
        if not chm.LoadCHM(chm_path):
            raise Exception("Failed to load CHM file.")
        
        text_content = []
        
        # Iterate through all files in the CHM
        for file_entry in chm:
            if file_entry.lower().endswith(('.html', '.htm')):
                content = chm.Extract(file_entry).decode('utf-8', errors='replace')
                
                # Use BeautifulSoup to clean HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                text_content.append(soup.get_text(separator='\n', strip=True))
        
        return '\n\n'.join(text_content)
    except Exception as e:
        raise Exception(f"PyCHM extraction failed: {e}")

def make_documents(text):
    return [Document(page_content=text)]

# === Load content ===
if SOURCE.endswith('.pdf'):
    raw_text = load_pdf(SOURCE)
elif SOURCE.startswith('http'):
    raw_text = load_html(SOURCE)
elif SOURCE.endswith('.chm'):
    raw_text = load_chm(SOURCE)  # Add CHM support
else:
    raise ValueError("Unsupported file format.")

# === Chunk + Embed ===
print("[+] Splitting and embedding...")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_documents(make_documents(raw_text))

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=CHROMA_DB_DIR)
retriever = vectordb.as_retriever()

# === Setup Ollama QA chain ===
llm = OllamaLLM(model=MODEL_NAME)
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# === Interactive Loop ===
print("\n✅ Assistant ready. Ask anything about the document.\n(Type 'exit' to quit.)")
while True:
    query = input("🧠 You: ")
    if query.lower() in ["exit", "quit"]:
        break
    answer = qa.invoke(query)
    print("🤖 Ollama:", answer)
