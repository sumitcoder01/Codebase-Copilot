import os
import logging
from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings # Using OpenAI's as a default high-quality embedder

log = logging.getLogger(__name__)

# Base directory to store all session-specific vector stores
SESSIONS_DIR = "sessions"

class VectorStoreManager:
    """
    Manages the creation, loading, and retrieval of vector stores for each session.
    """
    def __init__(self, session_id: str):
        """
        Initializes the manager for a specific session.

        Args:
            session_id (str): The unique identifier for the user's session.
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty.")
            
        self.session_id = session_id
        self.persist_directory = os.path.join(SESSIONS_DIR, self.session_id)
        
        # Using OpenAI's embedding model is a common and robust choice.
        # This could also be made configurable in the future.
        self.embedding_function = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        log.info(f"VectorStoreManager initialized for session '{session_id}' at '{self.persist_directory}'")

    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """
        Creates and persists a ChromaDB vector store from document chunks.

        Args:
            documents (List[Document]): A list of chunked documents to embed and store.

        Returns:
            Chroma: The created vector store instance.
        """
        log.info(f"Creating vector store for session '{self.session_id}'...")
        if not documents:
            log.warning("No documents provided to create vector store. It will be empty.")
            # Create an empty store so the directory is still made
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
        """
        Loads an existing vector store and returns a retriever interface.

        Returns:
            VectorStoreRetriever: A retriever ready to be used in a LangChain chain or agent.
        """
        log.info(f"Loading vector store for session '{self.session_id}' to create a retriever.")
        if not os.path.exists(self.persist_directory):
            log.error(f"Vector store not found for session '{self.session_id}' at path '{self.persist_directory}'")
            raise FileNotFoundError(f"Vector store for session {self.session_id} does not exist.")
            
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
        
        # Configure the retriever to find the top k most relevant chunks
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        log.info("Successfully created retriever from vector store.")
        return retriever