#chatbot.py
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
from indexer import index_pdf

document_path = Path("./ABNT_NBR_NORMA_BRASILEIRA.pdf")  # Altere para o nome do seu arquivo PDF

index_pdf(document_path)

# Carrega a base vetorial
embedding = OllamaEmbeddings(model="nomic-embed-text")
db = FAISS.load_local("banco_documento", embedding, allow_dangerous_deserialization=True)

# Instancia o modelo de linguagem
llm = ChatOllama(model="gemma3:4b")  # Pode trocar por mistral, llama3, etc

# Cria a chain de QA com recuperação
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=db.as_retriever()
)

# Loop de chat
print("❓ Pergunte algo sobre o documento (digite 'sair' para encerrar):")
while True:
    pergunta = input("🧠 Você: ")
    if pergunta.lower() == "sair":
        break
    resposta = qa.invoke(pergunta)
    print(f"🤖 IA: {resposta}\n")
