


def pick_assistant(file_type):
    """
    Function to select an assistant from a list of available assistants.
    """
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = None    
    # Return the selected assistant
    return selected_assistant