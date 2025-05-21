from langchain_ollama import OllamaEmbeddings, ChatOllama

def load_embedding_model():
    """
    Load the embedding model from Ollama.
    """
    # Load the embedding model
     # mxbai-embed-large or nomic-embed-text
    embed = OllamaEmbeddings(
        model="mxbai-embed-large"
    )
    return embed

def load_qa_model():
    """
    Load the question-answering model from Ollama.
    """
    # Load the question-answering model
    llm = ChatOllama(
        model="takenusername/gpt-4o-precise" #takenusername/gpt-4o-precise:latest - gemma3:4b - gemma3:1
    )
    return llm
    