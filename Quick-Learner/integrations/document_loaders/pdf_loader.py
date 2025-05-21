# pdf_loader.py
import os
import hashlib
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from ..model_loaders.simple_interpreter import load_embedding_model, load_qa_model
from ..helpers.chat_history import FileChatMessageHistory

def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

class ChatPDF:
    def __init__(self):
        self.vector_store = None
        self.chat_history = None
        self.llm = load_qa_model()
        self.embed = load_embedding_model()
        self.last_file_hash = None

    def ingest(self, file_path, progress_callback=None):
        file_hash = get_file_hash(file_path)
        vectorstore_path = f"./storage/faiss/{file_hash}"

        if self.last_file_hash == file_hash and os.path.exists(vectorstore_path):
            self.vector_store = FAISS.load_local(vectorstore_path, self.embed)
        else:
            self.last_file_hash = file_hash
            loader = PyPDFLoader(file_path)
            pages = list(loader.lazy_load())

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
            return "No document loaded. Please upload a PDF first."

        docs = self.vector_store.similarity_search(question, k=1) #usar 2 ou 3 pra melhorar a resposta
        
        history_text = "\n".join([
            f"{msg.type.upper()}: {msg.content}"
            for msg in self.chat_history.get_messages()
        ])
        
        context = "\n\n".join([doc.page_content for doc in docs]) + "\n\nChat History:\n" + history_text

        messages = [
            {"role": "system", "content": (
                "You are a trained model used as an assistant for general question-answering tasks. "
                "You can use the following pieces of context to answer the question (if relevant). "
                "If not, just answer based on your knowledge. Answer in the language of the question."
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

        # Save to history
        self.chat_history.add_message(HumanMessage(content=question))
        self.chat_history.add_message(SystemMessage(content=full_response))

    def clear(self):
        self.vector_store = None
        self.chat_history = None
