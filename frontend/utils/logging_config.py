import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# Create a dedicated logger for the frontend
# This avoids interfering with any other library's logging
log = logging.getLogger("frontend")
log.setLevel(logging.INFO)

def setup_logging():
    """
    Configures logging for the Streamlit frontend application.
    Logs to both console and a rotating file.
    This function should be called once at the start of the app.
    """
    # Prevent adding handlers multiple times on Streamlit re-runs
    if log.hasHandlers():
        log.info("Logger already configured. Skipping setup.")
        return

    # Create logs directory if it doesn't exist inside the frontend folder
    log_dir = os.path.join("frontend", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define log format
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    # --- File Handler ---
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "frontend.log"), 
        maxBytes=1024*1024*2, # 2 MB
        backupCount=3
    )
    file_handler.setFormatter(log_formatter)

    # Add handlers to the logger
    log.addHandler(console_handler)
    log.addHandler(file_handler)

    log.info("Frontend logging configured successfully.")