import pytest
from httpx import AsyncClient
from unittest.mock import patch

# Mark all tests in this file as asyncio tests
pytestmark = pytest.mark.asyncio


async def test_root_endpoint(test_client: AsyncClient):
    """Test the root endpoint to ensure the server is running."""
    response = await test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Codebase Copilot API!"}


async def test_upload_repo_success(test_client: AsyncClient, sample_codebase_zip: str, mock_llm_and_embeddings):
    """
    Test successful repository upload and processing.
    """
    with open(sample_codebase_zip, "rb") as f:
        files = {"file": ("test_repo.zip", f, "application/zip")}
        response = await test_client.post("/api/repo/upload", files=files)

    assert response.status_code == 200
    json_response = response.json()
    assert "session_id" in json_response
    assert json_response["message"] == "Repository processed successfully."
    
    # Verify that the session directories were created
    session_id = json_response["session_id"]
    assert os.path.exists(f"sessions/{session_id}")
    assert os.path.exists(f"sessions_code/{session_id}")
    assert os.path.exists(f"sessions_code/{session_id}/main.py")


async def test_chat_with_agent_success(test_client: AsyncClient, mock_llm_and_embeddings):
    """
    Test the chat endpoint with a valid session and query.
    We mock the graph stream to isolate the test to the API layer.
    """
    # Step 1: Create a mock session since we can't rely on a previous test run
    session_id = "mock-session-id"
    os.makedirs(f"sessions/{session_id}", exist_ok=True) # Mock session dir

    # Step 2: Mock the `stream_graph` function
    async def mock_stream_generator(*args, **kwargs):
        yield "This "
        yield "is a "
        yield "mocked response."

    # Use patch to replace the real stream_graph with our mock
    with patch('app.routes.chat.stream_graph', new=mock_stream_generator):
        # Step 3: Call the API
        response = await test_client.post(f"/api/chat/{session_id}", json={"query": "test query"})

    # Step 4: Assert the results
    assert response.status_code == 200
    assert response.text == "This is a mocked response."


async def test_chat_with_invalid_session(test_client: AsyncClient):
    """
    Test that the chat endpoint returns a 404 for a non-existent session.
    """
    session_id = "non-existent-session"
    response = await test_client.post(f"/api/chat/{session_id}", json={"query": "test query"})
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


async def test_chat_with_bad_request(test_client: AsyncClient):
    """
    Test that the chat endpoint returns a 422 for a malformed request body.
    """
    session_id = "some-session"
    # Missing the "query" key
    response = await test_client.post(f"/api/chat/{session_id}", json={"bad_key": "test query"})
    assert response.status_code == 422 # Unprocessable Entity