import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.chat import ChatMessageRequest
from app.services.decomposer import DecomposerService

@pytest.fixture
def test_client(mock_decomposer_service):
    """Create a test client with mocked decomposer service"""
    app.dependency_overrides[DecomposerService] = lambda: mock_decomposer_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_process_message(test_client):
    """Test chat message processing"""
    message = ChatMessageRequest(message="Test message")
    response = test_client.post(
        "/api/chat/message",
        json=message.model_dump()
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Test response structure
    assert data["message"] == message
    assert "id" in data
    assert "timestamp" in data
    assert "task_graph" in data
    
    # Test task graph structure (not content)
    task_graph = data["task_graph"]
    assert len(task_graph["tasks"]) == 2
    assert all(1 <= task["estimated_complexity"] <= 5 for task in task_graph["tasks"])

def test_get_chat_history(test_client):
    """Test chat history retrieval"""
    # First, send a message
    test_client.post(
        "/api/chat/message",
        json={"message": "Test message"}
    )
    
    # Then get history
    response = test_client.get("/api/chat/history")
    assert response.status_code == 200
    
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) >= 1
