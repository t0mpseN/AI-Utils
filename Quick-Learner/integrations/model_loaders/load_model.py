#load_model.py
import streamlit as st
from langchain_ollama import OllamaEmbeddings, ChatOllama

@st.cache_resource
def load_embedding_model(model_name="mxbai-embed-large"):
    """
    Load the embedding model from Ollama.
    """
    # Load the embedding model
    embed = OllamaEmbeddings(
        model=model_name # nomic-embed-text | mxbai-embed-large | all-minilm | gte-Qwen2-7B-instruct
    )
    return embed

@st.cache_resource
def load_assistant_model(model_name="gemma3:4b"):
    """
    Load the question-answering model from Ollama.
    """
    # Load the question-answering model
    llm = ChatOllama(
        model=model_name # gemma3:1b/gemma3:4b/gemma3:12b | codellama:7b/codellama:13b
    )
    return llm