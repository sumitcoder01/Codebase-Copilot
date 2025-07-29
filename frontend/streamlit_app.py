import streamlit as st
import requests
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

    if not BACKEND_URL:
        st.error("Backend URL is not configured.")
        st.stop()

    # --- Sidebar for Codebase Upload ---
    with st.sidebar:
        st.header("1. Start a New Session")
        tab1, tab2 = st.tabs(["From GitHub URL", "Upload ZIP"])

        with tab1:
            st.write("Analyze a public or private GitHub repository.")
            github_url = st.text_input("GitHub Repository URL", key="github_url_input", placeholder="https://github.com/user/repo")
            
            # Use a password field for the PAT for security
            pat = st.text_input("GitHub Personal Access Token (for private repos)", type="password", key="github_pat")

            with st.expander("What is a Personal Access Token?"):
                st.info(
                    "A Personal Access Token (PAT) is like a password for GitHub. "
                    "It allows this application to securely clone your private repository on your behalf. "
                    "Your token is used only for this cloning operation and is never stored."
                )
                st.markdown(
                    "**To create a token:**\n"
                    "1. Go to your GitHub Settings -> Developer settings -> Personal access tokens (classic).\n"
                    "2. Click 'Generate new token'.\n"
                    "3. Give it a name (e.g., 'CodebaseCopilot').\n"
                    "4. **Select the `repo` scope.** This is all that's needed.\n"
                    "5. Click 'Generate token' and copy the key."
                )

            if st.button("Analyze from URL"):
                if github_url and "github.com" in github_url:
                    with st.spinner("Cloning and processing repository..."):
                        try:
                            # Include the token in the payload if it exists
                            payload = {"repo_url": github_url, "token": pat if pat else None}
                            response = requests.post(f"{BACKEND_URL}/repo/clone", json=payload)
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.session_id = data["session_id"]
                                st.session_state.messages = []
                                st.success("Analysis complete!")
                                st.rerun()
                            else:
                                st.error(f"Error: {response.json().get('detail', 'Failed to process repository.')}")
                        
                        except requests.exceptions.RequestException as e:
                            st.error("Connection Error: Could not connect to the backend.")
                else:
                    st.warning("Please enter a valid GitHub URL.")

        with tab2:
            st.write("Upload a `.zip` file of your repository.")
            uploaded_file = st.file_uploader("Choose a .zip file", type="zip", label_visibility="collapsed")
            if uploaded_file is not None:
                if st.button("Analyze ZIP File"):
                    with st.spinner("Processing repository..."):
                        try:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/zip")}
                            response = requests.post(f"{BACKEND_URL}/repo/upload_zip", files=files)
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.session_id = data["session_id"]
                                st.session_state.messages = []
                                st.success("Analysis complete!")
                                st.rerun()
                            else:
                                st.error(f"Error: {response.json().get('detail', 'Failed to process repository.')}")
                        except requests.exceptions.RequestException as e:
                            st.error("Connection Error: Could not connect to the backend.")
    
    # --- Main Chat Interface (This part remains unchanged) ---
    if st.session_state.session_id:
        st.header(f"2. Ask Questions (Session: ...{st.session_state.session_id[-6:]})")
        # ... (the rest of the chat interface code is the same)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if prompt := st.chat_input("Ask about your codebase..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("The agent is thinking..."):
                    try:
                        data = {"query": prompt}
                        response = requests.post(f"{BACKEND_URL}/chat/{st.session_state.session_id}", json=data)
                        if response.status_code == 200:
                            full_response = response.text
                            st.markdown(full_response)
                        else:
                            full_response = f"Error: {response.json().get('detail', 'An unknown error occurred.')}"
                            st.error(full_response)
                    except requests.exceptions.RequestException as e:
                        full_response = "Connection Error: Could not get a response from the backend."
                        st.error(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        st.info("Start a new session from the sidebar to begin analyzing a codebase.")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()