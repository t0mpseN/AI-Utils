import os
import hashlib
import subprocess
import tempfile
import shutil
from datetime import datetime
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from ..model_loaders.load_model import load_embedding_model, load_assistant_model
from ..helpers.chat_history import FileChatMessageHistory


def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def extract_chm_with_7z(chm_path):
    temp_dir = tempfile.mkdtemp()
    seven_zip_path = r"C:/Program Files/7-Zip/7z.exe"  # ajuste conforme necessário

    if not os.path.exists(seven_zip_path):
        raise RuntimeError(f"7z.exe not found at {seven_zip_path}")

    try:
        subprocess.run([seven_zip_path, "x", chm_path, f"-o{temp_dir}"], check=True, stdout=subprocess.DEVNULL)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to extract CHM: {e}")

def load_chm(chm_path):
    extracted_dir = extract_chm_with_7z(chm_path)
    documents = []

    for root, _, files in os.walk(extracted_dir):
        for file in files:
            if file.endswith(".html") or file.endswith(".htm"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        documents.append(Document(page_content=content, metadata={"source": file_path}))
                except Exception:
                    continue

    return documents

class ChatCHM:
    def __init__(self):
        self.vector_store = None
        self.chat_history = None
        self.llm = load_assistant_model()
        self.embed = load_embedding_model()
        self.last_file_hash = None

    def ingest(self, file_path, progress_callback=None):
        file_hash = get_file_hash(file_path)
        vectorstore_path = f"./storage/faiss/{file_hash}"

        if os.path.exists(vectorstore_path):
            self.vector_store = FAISS.load_local(vectorstore_path, self.embed, allow_dangerous_deserialization=True)
        else:
            pages = load_chm(file_path)

            if progress_callback:
                progress_callback(0.3, "Generating embeddings...")

            self.vector_store = FAISS.from_documents(pages, self.embed)

            os.makedirs(vectorstore_path, exist_ok=True)
            self.vector_store.save_local(vectorstore_path)

            if progress_callback:
                progress_callback(1.0, "Ingestion complete!")

        session_id = f"session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        self.chat_history = FileChatMessageHistory("./storage/chat_history.json", session_id)

    def ask(self, question: str):
        if not self.vector_store or not self.chat_history:
            return "No document loaded. Please upload a CHM file first."

        docs = self.vector_store.similarity_search(question, k=2)

        history_text = "\n".join([
            f"{msg.type.upper()}: {msg.content}"
            for msg in self.chat_history.get_messages()
        ])
        
        context = "\n\n".join([doc.page_content for doc in docs]) + "\n\nChat History:\n" + history_text

        messages = [
            {"role": "system", "content": (
                "You are a trained model used as an assistant for GENERAL question-answering tasks. "
                "You can answer ANY question based on your own knowledge. "
                "ALWAYS answer in the same language as the question. "
                "Give a detailed answer, and if the question is not clear, ask for clarification. "
                "You can use the following pieces of context to answer the question if relevant. "
                "If the question is unrelated to the context, answer based on your knowledge. "
                "Always remember you can answer any question because you are a capable assistant. "
            )},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]

        full_response = ""
        for chunk in self.llm.stream(messages):
            content = chunk.content
            if content:
                content_str = str(content)
                full_response += content_str
                yield content_str

        self.chat_history.add_message(HumanMessage(content=question))
        self.chat_history.add_message(SystemMessage(content=full_response))

    def clear(self):
        self.vector_store = None
        self.chat_history = None
