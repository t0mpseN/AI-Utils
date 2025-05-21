#gui.py
import os
import tempfile
import streamlit as st
from streamlit_chat import message
from ..document_loaders.pdf_loader import ChatPDF

st.set_page_config(page_title="Quick Learner", page_icon="🤓")


def display_messages():
    st.subheader("Chat")
    for i, (msg, is_user) in enumerate(st.session_state["messages"]):
        if is_user:
            with st.chat_message("user"):
                st.write(msg)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg)
    st.session_state["thinking_spinner"] = st.empty()


def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        st.session_state["user_input"] = ""  # limpa o campo de input
        
        st.session_state["messages"].append((user_text, True))

        # Display an empty placeholder for streaming output
        response_placeholder = st.empty()
        streamed_response = ""
        response_placeholder.markdown("🔍 Processando pergunta...")

        for chunk in st.session_state["assistant"].ask(user_text):
            streamed_response += chunk
            response_placeholder.markdown(streamed_response + "▌")

        # Finalize the streamed response
        response_placeholder.markdown(streamed_response)
        st.session_state["messages"].append((streamed_response, False))

def read_and_save_file():
    st.session_state["assistant"].clear()
    st.session_state["messages"] = []
    st.session_state["user_input"] = ""

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
    if len(st.session_state) == 0:
        st.session_state["messages"] = []
        st.session_state["assistant"] = ChatPDF()

    st.header("Quick Learner")

    st.subheader("Upload a document")
    st.file_uploader(
        "Upload document",
        type=["pdf"],
        key="file_uploader",
        on_change=read_and_save_file,
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    st.session_state["ingestion_spinner"] = st.empty()

    display_messages()
    st.text_input("Message", key="user_input", on_change=process_input, placeholder="Digite sua pergunta aqui...")
