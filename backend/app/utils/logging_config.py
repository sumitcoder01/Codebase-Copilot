import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """
    Configures logging for the backend application.
    Logs to both console and a rotating file.
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define log format
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set the lowest level to capture all messages

    # --- Console Handler ---
    # Logs messages to the console (useful for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    
    # --- File Handler ---
    # Logs messages to a file, with rotation to prevent large files
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "backend.log"), 
        maxBytes=1024*1024*5, # 5 MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)

    # Add handlers to the root logger
    # Check if handlers are already added to avoid duplication in some environments
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    logging.info("Backend logging configured successfully.")