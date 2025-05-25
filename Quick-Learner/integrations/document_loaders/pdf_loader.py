# pdf_loader.py
import os
import hashlib
import time
from datetime import datetime
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.vectorstores.utils import DistanceStrategy
from ..model_loaders.load_model import load_embedding_model, load_assistant_model
from ..helpers.chat_history import FileChatMessageHistory

ASSISTANT_MODEL = "gemma3:4b"  # gemma3:1b/gemma3:4b/gemma3:12b | codellama:7b/codellama:13b
EMBEDDING_MODEL = "mxbai-embed-large"  # nomic-embed-text | mxbai-embed-large | all-minilm | gte-Qwen2-7B-instruct

def get_file_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def vectorstore_exists(path):
    return os.path.exists(os.path.join(path, "index.faiss")) and os.path.exists(os.path.join(path, "index.pkl"))

def load_pdf(file_path: str):
    """Load a single PDF file and return documents with source metadata."""
    loader = PyPDFLoader(file_path)
    docs = list(loader.lazy_load())
    for doc in docs:
        doc.metadata["source"] = os.path.basename(file_path)
        doc.metadata["file_hash"] = get_file_hash(file_path)
    return docs

def build_vector_store_with_progress(docs, embed_func, progress_callback=None) -> FAISS:
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
        self.vector_stores: Dict[str, FAISS] = {}
        self.chat_history = None
        self.llm = load_assistant_model(ASSISTANT_MODEL)
        self.embed = load_embedding_model(EMBEDDING_MODEL)
        self.loaded_files: Dict[str, str] = {}

    def ingest(self, file_paths: List[str], progress_callback=None):
        """Ingest multiple PDF files, each with its own vector store."""
        if not file_paths:
            raise ValueError("No files provided")

        # Ensure file_paths is always a list, even if single path is passed
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        total_files = len(file_paths)
        processed_files = 0

        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"The file {file_path} does not exist")

            try:
                file_hash = get_file_hash(file_path)
                print(f"File hash: {file_hash}")
                vectorstore_path = f"./storage/faiss/{file_hash}"

                if file_hash in self.vector_stores:
                    processed_files += 1
                    if progress_callback:
                        progress_callback(processed_files/total_files, f"Skipping existing file: {os.path.basename(file_path)}")
                    continue

                if vectorstore_exists(vectorstore_path):
                    # Load existing vector store
                    vector_store = FAISS.load_local(vectorstore_path, self.embed, allow_dangerous_deserialization=True)
                    if progress_callback:
                        progress_callback(processed_files/total_files, f"Loaded existing embeddings for: {os.path.basename(file_path)}")
                else:
                    # Create new vector store
                    if progress_callback:
                        progress_callback(processed_files/total_files, f"Processing: {os.path.basename(file_path)}")

                    pages = load_pdf(file_path)
                    vector_store = build_vector_store_with_progress(
                        pages, 
                        self.embed,
                        lambda pct, msg: progress_callback(
                            (processed_files + pct)/total_files,
                            f"{os.path.basename(file_path)}: {msg}"
                        ) if progress_callback else None
                    )
                    
                    os.makedirs(vectorstore_path, exist_ok=True)
                    vector_store.save_local(vectorstore_path)

                self.vector_stores[file_hash] = vector_store
                self.loaded_files[file_hash] = file_path
                processed_files += 1

                if progress_callback:
                    progress_callback(processed_files/total_files, f"Finished: {os.path.basename(file_path)}")

                session_id = f"session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                self.chat_history = FileChatMessageHistory("./storage/chat_history.json", session_id)

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                raise

    def ask(self, question: str):
        """Ask a question about all loaded documents."""
        if not self.vector_stores or not self.chat_history:
            yield "No documents loaded. Please upload PDFs first."
            return

        # Search across all vector stores
        all_docs = []
        for file_hash, vector_store in self.vector_stores.items():
            docs = vector_store.similarity_search(question, k=2)  # Get 2 chunks per document
            all_docs.extend(docs)

        # Organize context with source information
        context_parts = []
        for doc in all_docs:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"From {source}:\n{doc.page_content}")
        
        history_text = "\n".join([
            f"{msg.type.upper()}: {msg.content}"
            for msg in self.chat_history.get_messages()
        ])
        
        context = "\n\n".join(context_parts) + "\n\nChat History:\n" + history_text

        messages = [
            {"role": "system", "content": (
                "You are an assistant analyzing multiple documents. "
                "When answering questions, consider information from all provided documents. "
                "If information comes from a specific document, mention the source. "
                "Combine insights from different documents when appropriate. "
                "Answer in the same language as the question. "
                "Provide detailed responses and ask for clarification if needed."
            )},
            {"role": "user", "content": f"Context from documents:\n{context}\n\nQuestion: {question}"}
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

    def get_loaded_files(self) -> Dict[str, str]:
        """Get mapping of file hashes to file paths."""
        return self.loaded_files

    def get_file_vectorstore(self, file_hash: str):
        """Get the vector store for a specific file."""
        return self.vector_stores.get(file_hash)

    
