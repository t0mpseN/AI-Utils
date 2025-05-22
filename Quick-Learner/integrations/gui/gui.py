import os
import tempfile
import streamlit as st
import time
from streamlit_chat import message
from ..document_loaders.pdf_loader import ChatPDF

st.set_page_config(page_title="Quick Learner", page_icon="🤓", layout="wide")

def display_messages():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    messages = st.session_state["messages"]
    for msg, is_user in messages:
        if is_user:
            with st.chat_message("user"):
                st.write(msg)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg)
    if st.session_state.get("is_streaming", False):
        with st.chat_message("assistant"):
            if "streaming_placeholder" not in st.session_state:
                st.session_state["streaming_placeholder"] = st.empty()
            current_response = st.session_state.get("current_response", "🔍 Processando pergunta...")
            st.session_state["streaming_placeholder"].markdown(current_response + "▌")
    st.markdown('</div>', unsafe_allow_html=True)

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

def handle_streaming_response():
    """Handle the streaming response separately"""
    if st.session_state.get("is_streaming", False) and st.session_state.get("messages"):
        # Get the last user message
        user_messages = [msg for msg, is_user in st.session_state["messages"] if is_user]
        if user_messages:
            user_text = user_messages[-1]
            
            streamed_response = ""
            
            try:
                # Stream the response
                for chunk in st.session_state["assistant"].ask(user_text):
                    streamed_response += chunk
                    st.session_state["current_response"] = streamed_response
                    
                    # Update the streaming placeholder if it exists
                    if st.session_state.get("streaming_placeholder"):
                        st.session_state["streaming_placeholder"].markdown(streamed_response + "▌")
                
                # Finalize the response
                if st.session_state.get("streaming_placeholder"):
                    st.session_state["streaming_placeholder"].markdown(streamed_response)
                
                # Add to messages and clean up
                st.session_state["messages"].append((streamed_response, False))
                
            except Exception as e:
                error_msg = f"Erro ao processar: {str(e)}"
                if st.session_state.get("streaming_placeholder"):
                    st.session_state["streaming_placeholder"].markdown(error_msg)
                st.session_state["messages"].append((error_msg, False))
            
            finally:
                # Clean up streaming state
                st.session_state["is_streaming"] = False
                st.session_state["current_response"] = ""
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
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name
        
        progress_bar = st.progress(0, text=f"Ingesting {file.name}...")
        
        def update_progress(p, label=""):
            progress_bar.progress(p, text=label)

        st.session_state["assistant"].ingest(file_path, progress_callback=update_progress)
        
        os.remove(file_path)

def page():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = ChatPDF()
    if "is_streaming" not in st.session_state:
        st.session_state["is_streaming"] = False
    if "current_response" not in st.session_state:
        st.session_state["current_response"] = ""
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1], gap="small")
    
    with col1:
        display_messages()
        st.text_input("Message", key="user_input", on_change=process_input, placeholder="Digite sua pergunta aqui...")
    
    with col2:
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        st.subheader("Upload")
        uploaded_files = st.file_uploader(
            "Upload document",
            type=["pdf"],
            key="file_uploader",
            on_change=read_and_save_file,
            label_visibility="collapsed",
            accept_multiple_files=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle streaming response after the UI is set up
    handle_streaming_response()