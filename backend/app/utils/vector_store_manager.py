import os
import logging
import asyncio # <-- 1. Import asyncio
from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

log = logging.getLogger(__name__)
SESSIONS_DIR = "sessions"

class VectorStoreManager:
    """
    Manages the creation, loading, and retrieval of vector stores for each session.
    """
    def __init__(self, session_id: str):
        """
        Initializes the manager for a specific session.
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty.")
            
        self.session_id = session_id
        self.persist_directory = os.path.join(SESSIONS_DIR, self.session_id)
        
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set. It is required for embeddings.")
            
        # --- THE DEFINITIVE FIX FOR PARALLELISM ---
        # The GoogleGenerativeAIEmbeddings client requires an asyncio event loop to initialize,
        # but LangGraph runs parallel nodes in standard threads which don't have one.
        # This code block ensures an event loop is available in the current thread.
        try:
            # Check if an event loop is already running in this thread
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If not, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Now that an event loop is guaranteed to exist, we can safely initialize the client.
        self.embedding_function = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )

        log.info(f"VectorStoreManager initialized for session '{session_id}' using Gemini embeddings.")

    # ... (The rest of the file, create_vector_store and get_retriever, remains exactly the same)
    def create_vector_store(self, documents: List[Document]) -> Chroma:
        log.info(f"Creating vector store for session '{self.session_id}'...")
        if not documents:
            log.warning("No documents provided to create vector store. It will be empty.")
            vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
            )
            vector_store.persist()
            return vector_store
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            persist_directory=self.persist_directory
        )
        log.info(f"Successfully created and persisted vector store with {len(documents)} chunks.")
        return vector_store

    def get_retriever(self) -> VectorStoreRetriever:
        log.info(f"Loading vector store for session '{self.session_id}' to create a retriever.")
        if not os.path.exists(self.persist_directory):
            log.error(f"Vector store not found for session '{self.session_id}' at path '{self.persist_directory}'")
            raise FileNotFoundError(f"Vector store for session {self.session_id} does not exist.")
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        log.info("Successfully created retriever from vector store.")
        return retriever