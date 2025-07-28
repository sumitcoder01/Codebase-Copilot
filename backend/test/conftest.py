import pytest
import pytest_asyncio
import tempfile
import zipfile
import os
import shutil
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app object
from app.main import app

# --- Fixtures for Mocking External Services ---

@pytest.fixture(scope="module")
def mock_llm_and_embeddings():
    """
    Mocks the LLM and Embedding models to avoid actual API calls.
    This fixture will apply to all tests in a module.
    """
    # Mock for the LLM provider factory
    mock_get_llm = patch('app.llm.llm_provider.get_llm')
    
    # Mock for the embedding function used in the VectorStoreManager
    mock_openai_embeddings = patch('app.utils.vector_store_manager.OpenAIEmbeddings')

    with mock_get_llm as mocked_llm, mock_openai_embeddings as mocked_embeddings:
        # Configure the mocks to return a dummy object
        mocked_llm.return_value = MagicMock()
        mocked_embeddings.return_value = MagicMock()
        yield mocked_llm, mocked_embeddings


# --- Fixtures for Application and Test Data ---

@pytest_asyncio.fixture(scope="function")
async def test_client():
    """
    Creates an async test client for making API requests to the FastAPI app.
    This runs once per test function.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    # Cleanup session directories after each test function
    if os.path.exists("sessions"):
        shutil.rmtree("sessions")
    if os.path.exists("sessions_code"):
        shutil.rmtree("sessions_code")


@pytest.fixture(scope="function")
def sample_codebase_zip():
    """
    Creates a temporary zip file containing a dummy codebase.
    Yields the path to this zip file and cleans it up afterward.
    """
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip_file:
        zip_path = tmp_zip_file.name
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add a dummy Python file
            zf.writestr("main.py", 'def hello():\n    print("hello world")\n')
            # Add another file in a subdirectory
            zf.writestr("utils/helpers.py", 'def helper_function():\n    return True\n')

    yield zip_path

    # Cleanup: remove the temporary zip file
    os.remove(zip_path)