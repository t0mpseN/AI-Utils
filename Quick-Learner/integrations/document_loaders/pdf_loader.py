from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from ..model_loaders.simple_interpreter import load_embedding_model, load_qa_model
from ..helpers.chat_history import FileChatMessageHistory

def PDFLoader(file_path):
    # Load PDF pages
    loader = PyPDFLoader(file_path)
    pages = list(loader.lazy_load())

    # Load embedding model and build vector store
    embed = load_embedding_model()
    vector_store = InMemoryVectorStore.from_documents(pages, embed)

    # Store messages in chat history
    chat_history = FileChatMessageHistory("./storage/chat_history.json", f"session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    while True:
        # Ask user a question
        question = input("Ask a question ('q' to exit): ")

        if question.lower() == 'q':
            break

        # Find relevant documents
        docs = vector_store.similarity_search(question, k=2) 

        # Load LLM for answering
        llm = load_qa_model()

        # Prepare context for the LLM
        history_text = "\n".join([f"{msg.type.upper()}: {msg.content}" for msg in chat_history.get_messages()])
        context = "\n\n".join([doc.page_content for doc in docs]) + "\n\nChat History:\n" + history_text

        print(str(chat_history.get_messages()))

        # Format messages as list of dicts (correct format for most LangChain chat models)
        messages = [
            {"role": "system", "content": (
                "You are a trained model, used as an assistant for general question-answering tasks. "
                "You should answer any question asked with your current knowledge. "
                "You can use the following pieces of context to answer the question (if related to the context). "
                "If the question is not related to the context, ignore the context provided and give a proper answer with your own knowledge of a trained model. "
                "Answer in the language of the question."
                "Give a complete answer."
            )},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]

        # Get the answer from the LLM
        answer = llm.invoke(messages).content

        chat_history.add_message(HumanMessage(content=question))
        chat_history.add_message(SystemMessage(content=answer))

        print(f"Answer: {answer}")
