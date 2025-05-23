#simple_interpreter.py
import streamlit as st
from langchain_ollama import OllamaEmbeddings, ChatOllama

@st.cache_resource
def load_embedding_model(model_name="mxbai-embed-large"):
    """
    Load the embedding model from Ollama.
    """
    # Load the embedding model
     # mxbai-embed-large or nomic-embed-text
    embed = OllamaEmbeddings(
        model=model_name #nomic-embed-text e mxbai-embed-large
    )
    return embed

@st.cache_resource
def load_assistant_model(model_name="gemma3:1b"):
    """
    Load the question-answering model from Ollama.
    """
    # Load the question-answering model
    llm = ChatOllama(
        model=model_name #takenusername/gpt-4o-precise:latest - gemma3:4b - gemma3:12b - steamdj/llama3.1-cpu-only
    )
    return llm