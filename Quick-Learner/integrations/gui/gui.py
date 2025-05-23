#gui.py
import os
import tempfile
import streamlit as st
import time
from streamlit_chat import message
import streamlit.components.v1 as components
from ..document_loaders.pdf_loader import Assistant
from ..document_loaders.chm_loader import Assistant
from ..helpers.assistant_selector import pick_assistant

st.set_page_config(page_title="Quick Learner", page_icon="🤓", layout="wide")

def process_input():
    if st.session_state["user_input"].strip():
        user_text = st.session_state["user_input"].strip()
        st.session_state["user_input"] = ""
        st.session_state["messages"].append((user_text, True))
        
        # Initialize streaming state
        st.session_state["is_streaming"] = True
        st.session_state["current_response"] = "🔍 Processando pergunta..."
        
        # Clear any existing placeholder
        if "streaming_placeholder" in st.session_state:
            del st.session_state["streaming_placeholder"]

def read_and_save_file():
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""
    st.session_state["is_streaming"] = False
    st.session_state["current_response"] = ""
    
    # Clean up any existing placeholders
    if "streaming_placeholder" in st.session_state:
        del st.session_state["streaming_placeholder"]
    
    for file in st.session_state["file_uploader"]:
        # Get the file extension (without the dot)
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name
        
        progress_bar = st.progress(0, text=f"Ingesting {file.name}...")
        
        def update_progress(p, label=""):
            progress_bar.progress(p, text=label)

        st.session_state["assistant"].ingest(file_path, progress_callback=update_progress)
        
        os.remove(file_path)

def render_chat_interface():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    messages = st.session_state["messages"]
    
    for msg, is_user in messages:
        if is_user:
            with st.chat_message("user"):
                st.write(msg)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg)

    # Se estiver transmitindo, mostrar o placeholder
    if st.session_state.get("is_streaming", False):
        user_messages = [msg for msg, is_user in messages if is_user]
        if user_messages:
            user_text = user_messages[-1]
            streamed_response = ""
            
            with st.chat_message("assistant"):
                if "streaming_placeholder" not in st.session_state:
                    st.session_state["streaming_placeholder"] = st.empty()
                placeholder = st.session_state["streaming_placeholder"]

                try:
                    for chunk in st.session_state["assistant"].ask(user_text):
                        streamed_response += chunk
                        st.session_state["current_response"] = streamed_response
                        placeholder.markdown(streamed_response + "▌")

                    placeholder.markdown(streamed_response)
                    st.session_state["messages"].append((streamed_response, False))
                except Exception as e:
                    error_msg = f"Erro ao processar: {str(e)}"
                    placeholder.markdown(error_msg)
                    st.session_state["messages"].append((error_msg, False))
                finally:
                    st.session_state["is_streaming"] = False
                    st.session_state["current_response"] = ""
                    del st.session_state["streaming_placeholder"]

    st.markdown('</div>', unsafe_allow_html=True)

def get_file_extension(uploaded_file):
    """Returns the file extension in lowercase without the dot"""
    return os.path.splitext(uploaded_file.name)[1][1:].lower()

def page():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = None #change this based on the file type (call function to pick assistant)
    if "is_streaming" not in st.session_state:
        st.session_state["is_streaming"] = False
    if "current_response" not in st.session_state:
        st.session_state["current_response"] = ""

    # Sidebar fixa com upload de documentos
    with st.sidebar:
        st.subheader("📄 Upload de Documentos")
        uploaded_files = st.file_uploader(
            "Selecionar arquivos",
            type=["pdf", "chm"],
            key="file_uploader",
            on_change=read_and_save_file,
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        # Set the assistant based on the first uploaded file (if any)
    if uploaded_files and st.session_state["file_uploader"]:
        first_file = st.session_state["file_uploader"][0]
        file_extension = get_file_extension(first_file)
        st.session_state["assistant"] = pick_assistant(file_type=file_extension)
    elif st.session_state["assistant"] is None:
        # Default to PDF assistant if no files uploaded yet
        st.session_state["assistant"] = pick_assistant(file_type="pdf")

    # Layout principal: uma coluna para o chat
    col1, col2 = st.columns([0.1, 30])  # Sidebar já é fixa; col1 vazio deixa col2 com tudo

    with col2:
        st.markdown("## 💬 Chat")
        chat_container = st.container()
        with chat_container:
            render_chat_interface()
            #display_messages()
            #handle_streaming_response()
            st.text_input(
                "Mensagem",
                key="user_input",
                on_change=process_input,
                placeholder="Digite sua pergunta aqui..."
            )
