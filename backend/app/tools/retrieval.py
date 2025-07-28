import logging
from langchain.tools import Tool
from langchain.tools.retriever import create_retriever_tool
from app.utils.vector_store_manager import VectorStoreManager

log = logging.getLogger(__name__)

def get_retriever_tool(session_id: str) -> Tool:
    """
    Creates and returns a retriever tool for a specific session.
    This tool allows an agent to query the vector store of the codebase.

    Args:
        session_id (str): The unique identifier for the user's session.

    Returns:
        Tool: A LangChain tool configured for semantic retrieval.
    """
    log.info(f"Creating retriever tool for session_id: {session_id}")
    
    try:
        # Initialize the vector store manager for the given session
        vsm = VectorStoreManager(session_id=session_id)
        
        # Get the retriever interface from the manager
        retriever = vsm.get_retriever()
        
        # Create a pre-packaged retriever tool
        # The description is crucial, as it tells the agent *when* to use this tool.
        tool = create_retriever_tool(
            retriever,
            "codebase_retriever",
            (
                "Searches and retrieves relevant code snippets, file contents, or summaries "
                "from the codebase vector store. Use this to answer questions about "
                "how the code works, what a specific function does, or where certain logic is located."
            ),
        )
        log.info(f"Retriever tool for session '{session_id}' created successfully.")
        return tool
    except FileNotFoundError as e:
        log.error(f"Failed to create retriever tool for session '{session_id}': Vector store not found. {e}")
        # Return a dummy tool or handle this gracefully in the agent creation logic
        raise
    except Exception as e:
        log.error(f"An unexpected error occurred while creating the retriever tool for session '{session_id}': {e}", exc_info=True)
        raise