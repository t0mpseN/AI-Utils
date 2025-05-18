import os
import sys
import io
import time
import shutil
import pickle
import subprocess
import traceback
import json
import chromadb
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

# === Configurações ===
if len(sys.argv) < 2:
    print("Erro: caminho do arquivo não informado.")
    sys.exit(1)

SOURCE = sys.argv[1]
CHROMA_DB_DIR = "./chroma_db"
CACHE_TEXT_FILE = "text_cache.txt"
CACHE_CHM_DIR = "./.cache_chm_extracted"
CACHE_CHUNKS_FILE = "chunks.pkl"
MODEL_NAME = "gemma3:12b"

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def extract_text_from_pdf(path):
    log(f"[=] Extraindo texto de PDF: {path}")
    reader = PdfReader(path)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

def extract_text_from_html(path):
    log(f"[=] Extraindo texto de HTML: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        return soup.get_text()
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
        log("[✓] Arquivos extraídos.")
    else:
        log("[✓] Arquivos HTML já extraídos.")

    html_files = list(Path(CACHE_CHM_DIR).rglob("*.htm")) + list(Path(CACHE_CHM_DIR).rglob("*.html"))
    log(f"[✓] {len(html_files)} arquivos HTML encontrados.")
    return html_files

def load_text_from_file(path):
    if path.endswith(".chm"):
        return load_cached_or_extract_chm_text(path)
    elif path.endswith(".pdf"):
        return extract_text_from_pdf(path)
    elif path.endswith(".html") or path.endswith(".htm"):
        return extract_text_from_html(path)
    else:
        raise ValueError("Formato de arquivo não suportado.")

def load_cached_or_extract_chm_text(path):
    if os.path.exists(CACHE_TEXT_FILE):
        log("[✓] Cache de texto encontrado. Carregando...")
        with open(CACHE_TEXT_FILE, "r", encoding="utf-8") as f:
            return f.read()

    html_files = extract_chm_to_html(path)
    all_texts = []

    for file in tqdm(html_files, desc="Lendo arquivos .html", unit="arquivo"):
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
        log("[✓] Chunks (docs) já existentes. Carregando do cache...")
        with open(CACHE_CHUNKS_FILE, "rb") as f:
            return pickle.load(f)

    log("[=] Dividindo texto em chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(make_documents(text))

    for _ in tqdm(range(len(docs)), desc="Criando chunks", unit="chunk"):
        pass  # apenas para mostrar progresso

    with open(CACHE_CHUNKS_FILE, "wb") as f:
        pickle.dump(docs, f)

    return docs

# === Prompt customizado ===
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful assistant with general knowledge and can also use the following documentation to give a proper answer (if the user asks about it):

{context}

Question: {question}
Answer:
"""
)

# === Main ===
log("[>] Iniciando carregamento dos documentos...")
raw_text = load_text_from_file(SOURCE)
docs = get_or_create_chunks(raw_text)

log("[=] Carregando modelo de embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
    log("[\u2713] Carregando banco de embeddings salvo...")
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
else:
    log("[=] Gerando novos embeddings e salvando...")
    # tqdm apenas para indicar progresso geral
    with tqdm(total=len(docs), desc="Gerando embeddings", unit="chunk") as pbar:
        def callback(_):
            pbar.update(1)
        vectordb = Chroma.from_documents(
            docs,
            embedding=embeddings,
            persist_directory=CHROMA_DB_DIR,
            ids=[str(i) for i in range(len(docs))],
        )

retriever = vectordb.as_retriever()

log("[=] Carregando modelo Ollama...")
llm = OllamaLLM(model=MODEL_NAME)

chain = LLMChain(llm=llm, prompt=prompt_template)

# === Loop interativo ===
log("✅ Assistente pronto! Pergunte algo sobre a documentação ou qualquer outro assunto.\n(Digite 'exit' para sair.)")

while True:
    raw = input()
    if raw.strip().lower() == "exit":
        break
    try:
        data = json.loads(raw)
        question = data.get("question", "")
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = chain.invoke({"context": context, "question": question})
        print(json.dumps({"answer": answer["text"]}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))