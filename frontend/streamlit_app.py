import streamlit as st
import requests
import time
import os
import sys
from dotenv import load_dotenv


# Load environment variables from the .env file in the project root
load_dotenv()

# Add the root directory to the Python path to allow importing from 'frontend.utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Now we can import our logging utility
    from frontend.utils.logging_config import setup_logging, log
    # Configure logging
    setup_logging()
except ImportError:
    # Fallback to basic logging if the util is not found
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

# Load the backend URL from environment variables, with a fallback for safety
BACKEND_URL = os.getenv("STREAMLIT_BACKEND_URL", "http://127.0.0.1:8000/api")

# Set the page configuration
st.set_page_config(
    page_title="Codebase Copilot",
    page_icon="🤖",
    layout="wide"
)

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Main Application Logic ---

def main():
    """Main function to run the Streamlit application."""
    st.title("🤖 Codebase Copilot")
    st.caption("Your AI-powered assistant for understanding any codebase.")

    # Check if the backend URL is properly configured
    if "127.0.0.1" in BACKEND_URL:
        st.sidebar.info("Running in local development mode.")
    if not BACKEND_URL:
        st.error("Backend URL is not configured. Please set STREAMLIT_BACKEND_URL in your .env file.")
        st.stop() # Halt the app if the backend URL is missing

    # --- Sidebar for Codebase Upload ---
    with st.sidebar:
        st.header("1. Upload Your Codebase")
        st.write(
            "Upload a `.zip` file of your repository. "
            "A new session will be created for analysis."
        )
        
        uploaded_file = st.file_uploader(
            "Choose a .zip file", type="zip", label_visibility="collapsed"
        )

        if uploaded_file is not None:
            if st.button("Analyze Codebase"):
                with st.spinner("Processing repository... This may take a moment."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                        response = requests.post(f"{BACKEND_URL}/repo/upload", files=files)

                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.session_id = data["session_id"]
                            st.session_state.messages = [] # Reset chat history
                            log.info(f"New session started: {st.session_state.session_id}")
                            st.success("Analysis complete! You can now ask questions about your code.")
                            st.rerun() # Rerun to switch to the chat view
                        else:
                            log.error(f"Backend error on upload: {response.text}")
                            st.error(f"Error: {response.json().get('detail', 'Failed to process repository.')}")
                    
                    except requests.exceptions.RequestException as e:
                        log.error(f"Could not connect to backend: {e}")
                        st.error("Connection Error: Could not connect to the backend. Please ensure it's running.")

    # --- Main Chat Interface ---
    if st.session_state.session_id:
        st.header(f"2. Ask Questions (Session: ...{st.session_state.session_id[-6:]})")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about your codebase... (e.g., 'Find bugs in main.py')"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    data = {"query": prompt}
                    with requests.post(
                        f"{BACKEND_URL}/chat/{st.session_state.session_id}",
                        json=data,
                        stream=True,
                    ) as r:
                        if r.status_code == 200:
                            for chunk in r.iter_content(chunk_size=None):
                                full_response += chunk.decode('utf-8')
                                message_placeholder.markdown(full_response + "▌")
                            message_placeholder.markdown(full_response)
                        else:
                            log.error(f"Chat error from backend: {r.text}")
                            full_response = f"Error: {r.json().get('detail', 'An unknown error occurred.')}"
                            message_placeholder.error(full_response)

                except requests.exceptions.RequestException as e:
                    log.error(f"Could not connect to backend during chat: {e}")
                    full_response = "Connection Error: Could not get a response from the backend."
                    message_placeholder.error(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    else:
        st.info("Upload a zipped codebase in the sidebar to begin.")

if __name__ == "__main__":
    main()