#simple_interpreter.py
import streamlit as st
from langchain_ollama import OllamaEmbeddings, ChatOllama

@st.cache_resource
def load_embedding_model():
    """
    Load the embedding model from Ollama.
    """
    # Load the embedding model
     # mxbai-embed-large or nomic-embed-text
    embed = OllamaEmbeddings(
        model="mxbai-embed-large" #nomic-embed-text e mxbai-embed-large
    )
    return embed

@st.cache_resource
def load_qa_model():
    """
    Load the question-answering model from Ollama.
    """
    # Load the question-answering model
    llm = ChatOllama(
        model="gemma3:4b" #takenusername/gpt-4o-precise:latest - gemma3:4b - gemma3:12b - steamdj/llama3.1-cpu-only
    )
    return llm