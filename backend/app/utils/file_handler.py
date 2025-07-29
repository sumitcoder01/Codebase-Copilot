import os
import zipfile
import logging
from typing import List
import git
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

log = logging.getLogger(__name__)

# Supported file extensions for code processing
SUPPORTED_EXTENSIONS = [
    ".py", ".java", ".js", ".ts", ".html", ".css", ".md", ".json", ".yaml", ".yml", ".c", ".cpp", ".cs"
]

def extract_zip(zip_path: str, extract_to: str) -> None:
    """
    Extracts the contents of a zip file to a specified directory.

    Args:
        zip_path (str): The path to the zip file.
        extract_to (str): The directory where contents should be extracted.
    """
    log.info(f"Extracting zip file from '{zip_path}' to '{extract_to}'...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        log.info("Successfully extracted zip file.")
    except Exception as e:
        log.error(f"Failed to extract zip file: {e}", exc_info=True)
        raise

def load_and_chunk_codebase(repo_path: str) -> List[Document]:
    """
    Walks through a directory, loads supported code files, and splits them into chunks.

    Args:
        repo_path (str): The path to the extracted codebase directory.

    Returns:
        List[Document]: A list of Document objects, each representing a chunk of code.
    """
    log.info(f"Loading and chunking codebase from path: {repo_path}")
    documents = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Create a single document for the whole file content
                    # We store the relative path in the metadata for easy identification
                    relative_path = os.path.relpath(file_path, repo_path)
                    doc = Document(page_content=content, metadata={"source": relative_path})
                    documents.append(doc)
                    log.debug(f"Loaded file: {relative_path}")
                except Exception as e:
                    log.warning(f"Could not read file {file_path}: {e}")

    # Initialize a text splitter for code
    code_splitter = RecursiveCharacterTextSplitter.from_language(
        language="python", # A generic choice, adaptable for many languages
        chunk_size=2000,
        chunk_overlap=200
    )
    
    chunked_documents = code_splitter.split_documents(documents)
    log.info(f"Finished chunking. Total documents: {len(documents)}, Total chunks: {len(chunked_documents)}")
    
    return chunked_documents

def clone_github_repo(repo_url: str, clone_to: str) -> None:
    """
    Clones a public GitHub repository to a specified local path.

    Args:
        repo_url (str): The URL of the public GitHub repository.
        clone_to (str): The local directory to clone the repository into.
    """
    log.info(f"Cloning GitHub repository from '{repo_url}' to '{clone_to}'...")
    try:
        git.Repo.clone_from(repo_url, clone_to)
        log.info("Successfully cloned repository.")
    except git.exc.GitCommandError as e:
        log.error(f"Failed to clone repository: {e}", exc_info=True)
        # Provide a more user-friendly error message
        raise RuntimeError(f"Failed to clone repository. Please ensure it is a valid public URL.")
    except Exception as e:
        log.error(f"An unexpected error occurred during cloning: {e}", exc_info=True)
        raise