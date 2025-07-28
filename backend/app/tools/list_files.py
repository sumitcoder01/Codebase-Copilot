import os
import logging
from typing import Type, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Directory where extracted code for sessions is stored
SESSIONS_CODE_DIR = "sessions_code"

class ListFilesToolInput(BaseModel):
    """Input schema for the ListFilesTool."""
    directory: Optional[str] = Field(
        default=".",
        description="The relative directory path to list files from. Defaults to the root.",
    )

class ListFilesTool(BaseTool):
    """
    A tool to list files and directories within the codebase.
    This provides visibility into the project structure.
    """
    name: str = "list_files"
    description: str = (
        "Lists all files and directories within a specified path of the codebase. "
        "Use this to explore the project structure and find correct file paths."
    )
    args_schema: Type[BaseModel] = ListFilesToolInput
    session_id: str

    def _run(self, directory: str = ".") -> str:
        """Executes the tool to list directory contents."""
        session_code_path = os.path.join(SESSIONS_CODE_DIR, self.session_id)
        
        # Security: Prevent path traversal attacks
        target_path = os.path.abspath(os.path.join(session_code_path, directory))
        if not target_path.startswith(os.path.abspath(session_code_path)):
            return "Error: Access denied. Path is outside the allowed project directory."

        log.info(f"Agent listing files in: '{target_path}' for session '{self.session_id}'")
        
        try:
            if not os.path.isdir(target_path):
                return f"Error: '{directory}' is not a valid directory."
            
            contents = os.listdir(target_path)
            if not contents:
                return f"The directory '{directory}' is empty."
            
            return "\n".join(contents)
        except FileNotFoundError:
            return f"Error: Directory '{directory}' not found."
        except Exception as e:
            log.error(f"Error listing files in {target_path}: {e}", exc_info=True)
            return "An unexpected error occurred while listing files."

    async def _arun(self, directory: str = ".") -> str:
        """Asynchronous version of the tool's execution."""
        return self._run(directory)