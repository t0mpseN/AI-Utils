# pdf_loader.py
import os
import hashlib
import time
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.vectorstores.utils import DistanceStrategy
from ..model_loaders.load_model import load_embedding_model, load_assistant_model
from ..helpers.chat_history import FileChatMessageHistory

def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def vectorstore_exists(path):
    return os.path.exists(os.path.join(path, "index.faiss")) and os.path.exists(os.path.join(path, "index.pkl"))

def build_vector_store_with_progress(docs, embed_func, progress_callback=None):
    docs_with_embeddings = []
    total = len(docs)

    print(f"Iniciando embedding de {total} documentos...")

    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]
    batch_size = 32  # pode ajustar conforme o modelo usado

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_texts = texts[start:end]
        batch_embeddings = embed_func.embed_documents(batch_texts)

        for i, emb in enumerate(batch_embeddings):
            idx = start + i
            docs_with_embeddings.append((docs[idx], emb))

            if progress_callback:
                pct = 0.3 + 0.6 * (idx / total)
                progress_callback(pct, f"Embedding document {idx+1}/{total}")

    print("Todos os embeddings foram gerados.")

    if not docs_with_embeddings:
        raise ValueError("Nenhum embedding foi gerado.")

    text_embeddings = [(doc.page_content, emb) for doc, emb in docs_with_embeddings]
    embeddings = [emb for _, emb in text_embeddings]
    
    print("Iniciando criação da vector store (FAISS.from_texts)...")
    start_time = time.time()
    
    try:
        # Create the FAISS index directly with texts and embeddings
        vectorstore = FAISS.from_embeddings(
            text_embeddings=text_embeddings,
            embedding=embed_func,
            metadatas=metadatas,
            distance_strategy=DistanceStrategy.COSINE,
        )
    except Exception as e:
        print(f"Erro ao criar vector store: {e}")
        raise

    end_time = time.time()
    print(f"Vector store criada com sucesso em {end_time - start_time:.2f} segundos.")

    return vectorstore

class ChatPDF:
    def __init__(self):
        self.vector_store = None
        self.chat_history = None
        self.llm = load_assistant_model("gemma3:4b")
        self.embed = load_embedding_model("mxbai-embed-large")
        self.last_file_hash = None

    def ingest(self, file_path, progress_callback=None):
        file_hash = get_file_hash(file_path)
        vectorstore_path = f"./storage/faiss/{file_hash}"

        if vectorstore_exists(vectorstore_path):
            self.vector_store = FAISS.load_local(vectorstore_path, self.embed, allow_dangerous_deserialization=True)
            if progress_callback:
                progress_callback(1.0, "Ingestion complete!")
        else:
            loader = PyPDFLoader(file_path)
            pages = list(loader.lazy_load())

            if progress_callback:
                progress_callback(0.3, "Generating embeddings...")

            self.vector_store = build_vector_store_with_progress(pages, self.embed, progress_callback)
            os.makedirs(vectorstore_path, exist_ok=True)
            try:
                os.makedirs(vectorstore_path, exist_ok=True)
                self.vector_store.save_local(vectorstore_path)
                print("FAISS salvo com sucesso.")
            except Exception as e:
                print(f"Erro ao salvar FAISS: {e}")
                raise

            if progress_callback:
                progress_callback(1.0, "Ingestion complete!")

        session_id = f"session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        self.chat_history = FileChatMessageHistory("./storage/chat_history.json", session_id)


    def ask(self, question: str):
        if not self.vector_store or not self.chat_history:
            return "No document loaded. Please upload a PDF first."

        docs = self.vector_store.similarity_search(question, k=2) #usar 2 ou 3 pra melhorar a resposta
        
        #retriever = self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        #docs = retriever.get_relevant_documents(question)
   
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

        # Save to history
        self.chat_history.add_message(HumanMessage(content=question))
        self.chat_history.add_message(SystemMessage(content=full_response))

    def clear(self):
        self.vector_store = None
        self.chat_history = None
