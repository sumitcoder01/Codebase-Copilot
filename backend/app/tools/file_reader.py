import os
import logging
from typing import Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Base directory for all user sessions and their extracted code
SESSIONS_CODE_DIR = "sessions_code"

class ReadFileToolInput(BaseModel):
    """Input schema for the ReadFileTool."""
    file_path: str = Field(description="The relative path to the file within the codebase.")

class ReadFileTool(BaseTool):
    """
    A tool to read the content of a specific file from the codebase.
    This tool is sandboxed to the session's code directory for security.
    """
    name: str = "read_file"
    description: str = (
        "Reads the entire content of a specified file. "
        "Use this to get the code from a file before debugging, refactoring, or analyzing it."
    )
    args_schema: Type[BaseModel] = ReadFileToolInput
    session_id: str

    def _run(self, file_path: str) -> str:
        """Executes the tool to read the file content."""
        session_code_path = os.path.join(SESSIONS_CODE_DIR, self.session_id)
        
        # Security: Create the absolute path and ensure it's within the session's directory.
        full_path = os.path.abspath(os.path.join(session_code_path, file_path))
        
        if not full_path.startswith(os.path.abspath(session_code_path)):
            log.warning(f"Attempted path traversal attack by agent: {file_path}")
            return "Error: Access denied. You can only access files within the codebase."

        log.info(f"Agent reading file: '{full_path}' for session '{self.session_id}'")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            log.error(f"File not found by agent: {full_path}")
            return f"Error: File '{file_path}' not found."
        except Exception as e:
            log.error(f"Error reading file {full_path}: {e}", exc_info=True)
            return f"Error: Could not read file '{file_path}'."

    async def _arun(self, file_path: str) -> str:
        """Asynchronous version of the tool's execution."""
        # For this I/O bound operation, we can reuse the synchronous implementation
        return self._run(file_path)