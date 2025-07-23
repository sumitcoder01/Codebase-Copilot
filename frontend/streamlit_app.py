# --- Initial Setup: Logging and Page Configuration ---

import streamlit as st

# Set up logging before anything else
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import and use our logging utility
from frontend.utils.logging_config import setup_logging, log

# Configure logging
setup_logging()

# Set the page configuration
# This must be the first Streamlit command called
st.set_page_config(
    page_title="Codebase Copilot",
    page_icon="🤖",
    layout="wide"
)

# --- Main Application Logic Starts Here ---

log.info("Streamlit app started.")

st.title("🤖 Codebase Copilot")
