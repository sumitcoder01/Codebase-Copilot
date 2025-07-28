import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.utils.logging_config import setup_logging
from app.routes.chat import router as chat_router

# --- Application Setup ---

# Load environment variables from .env file
load_dotenv()

# Set up logging for the entire backend
setup_logging()

# Get a logger for the main application
log = logging.getLogger(__name__)

# Create the FastAPI application instance
app = FastAPI(
    title="Codebase Copilot Backend",
    description="API for the multi-agent Codebase Copilot application.",
    version="1.0.0"
)

# --- Middleware Configuration ---

# Configure CORS (Cross-Origin Resource Sharing)
# This is crucial for allowing the Streamlit frontend to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity. For production, restrict this.
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# --- API Routers ---

# Include the chat router, which contains our /upload and /chat endpoints
app.include_router(chat_router, prefix="/api")

# --- Root Endpoint ---

@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    log.info("Root endpoint was accessed.")
    return {"message": "Welcome to the Codebase Copilot API!"}
