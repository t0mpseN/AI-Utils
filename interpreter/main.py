import os
import sys
import io
import time
import shutil
import pickle
import subprocess
import traceback
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

# === Configurações ===
SOURCE = "RevitAPI.chm"
CHROMA_DB_DIR = "./chroma_db"
CACHE_TEXT_FILE = "revit_text_cache.txt"
CACHE_CHM_DIR = "./.cache_chm_extracted"
CACHE_CHUNKS_FILE = "revit_chunks.pkl"
MODEL_NAME = "gemma3:12b"

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# === Carregamento ou extração do CHM ===
def extract_chm_to_html(path):
    if not os.path.exists(CACHE_CHM_DIR):
        os.makedirs(CACHE_CHM_DIR, exist_ok=True)
        log("[=] Extraindo .chm com 7-Zip...")
        subprocess.run(
            [r"C:\\Program Files\\7-Zip\\7z.exe", "x", path, f"-o{CACHE_CHM_DIR}"],
            check=True,
            stdout=subprocess.DEVNULL
        )
        log("[\u2713] Arquivos extraídos.")
    else:
        log("[\u2713] Arquivos HTML já extraídos.")

    return list(Path(CACHE_CHM_DIR).rglob("*.htm")) + list(Path(CACHE_CHM_DIR).rglob("*.html"))

def load_cached_or_extract_chm_text(path):
    if os.path.exists(CACHE_TEXT_FILE):
        log("[\u2713] Cache de texto encontrado. Carregando...")
        with open(CACHE_TEXT_FILE, "r", encoding="utf-8") as f:
            return f.read()

    html_files = extract_chm_to_html(path)
    log(f"[=] Lendo arquivos HTML ({len(html_files)} arquivos)...")
    all_texts = []

    for file in tqdm(html_files, desc="Processando .html"):
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                all_texts.append(soup.get_text())
        except Exception as e:
            print(f"[!] Falha ao ler {file}: {e}")

    full_text = "\n".join(all_texts)
    with open(CACHE_TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)

    return full_text

def make_documents(text):
    return [Document(page_content=text)]

def get_or_create_chunks(text):
    if os.path.exists(CACHE_CHUNKS_FILE):
        log("[\u2713] Chunks (docs) já existentes. Carregando do cache...")
        with open(CACHE_CHUNKS_FILE, "rb") as f:
            return pickle.load(f)

    log("[=] Dividindo texto em chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(make_documents(text))

    with open(CACHE_CHUNKS_FILE, "wb") as f:
        pickle.dump(docs, f)

    return docs

# === Prompt customizado ===
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Você é um assistente com conhecimento geral e também acesso à seguinte documentação (se relevante):

{context}

Pergunta: {question}
Resposta:
"""
)

# === Main ===
log("[>] Iniciando carregamento dos documentos...")
raw_text = load_cached_or_extract_chm_text(SOURCE)
docs = get_or_create_chunks(raw_text)

log("[=] Carregando modelo de embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
    log("[\u2713] Carregando banco de embeddings salvo...")
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
else:
    log("[=] Gerando novos embeddings e salvando...")
    vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=CHROMA_DB_DIR)

retriever = vectordb.as_retriever()

log("[=] Carregando modelo Ollama...")
llm = OllamaLLM(model=MODEL_NAME)

chain = LLMChain(llm=llm, prompt=prompt_template)

log("\u2705 Assistente pronto! Pergunte algo sobre a documentação ou qualquer outro assunto.\n(Digite 'exit' para sair.)")

# === Loop interativo ===
log("✅ Assistente pronto! Pergunte algo sobre a documentação ou qualquer outro assunto.\n(Digite 'exit' para sair.)")

while True:
    query = input("🧠 Você: ")
    if query.lower() in ["exit", "quit"]:
        break

    try:
        log("[=] Buscando trechos relevantes...")
        start = time.time()
        docs = retriever.get_relevant_documents(query)
        context = "\n\n".join([doc.page_content for doc in docs])

        log(f"[=] Gerando resposta (usando {len(docs)} trechos)...")
        answer = chain.invoke({"context": context, "question": query})
        end = time.time()

        print(f"🤖 Ollama ({end - start:.2f}s):\n{answer['text']}")
    except Exception:
        print("[!] Ocorreu um erro:")
        traceback.print_exc()