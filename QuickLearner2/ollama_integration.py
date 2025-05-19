from langchain_ollama import OllamaLLM

def setup_llm(model_name):
    # Initialize Ollama with your preferred model
    return OllamaLLM(model=model_name)