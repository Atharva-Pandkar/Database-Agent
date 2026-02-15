import pytest
from datetime import datetime
from app.schemas.decomposer import TaskNode, TaskGraph, TaskStatus, DecompositionRequest
from pydantic import ValidationError

def test_task_node_validation():
    """Test TaskNode validation"""
    # Test valid task node
    task = TaskNode(
        id="123",
        title="Test Task",
        description="Test Description",
        estimated_complexity=3,
        dependencies=[]
    )
    assert task.id == "123"
    assert task.status == TaskStatus.PENDING
    assert task.estimated_complexity == 3

    # Test complexity validation
    with pytest.raises(ValidationError):
        TaskNode(
            id="123",
            title="Test Task",
            description="Test Description",
            estimated_complexity=6  # Should be 1-5
        )

def test_task_graph_validation():
    """Test TaskGraph validation"""
    task = TaskNode(
        id="123",
        title="Test Task",
        description="Test Description",
        estimated_complexity=3
    )
    
    graph = TaskGraph(
        id="graph-123",
        query="test query",
        tasks=[task]
    )
    
    assert graph.id == "graph-123"
    assert len(graph.tasks) == 1
    assert isinstance(graph.created_at, datetime)

def test_decomposition_request_validation():
    """Test DecompositionRequest validation"""
    # Test with required fields only
    request = DecompositionRequest(query="test query")
    assert request.query == "test query"
    assert request.context == {}

    # Test with context
    request = DecompositionRequest(
        query="test query",
        context={"key": "value"}
    )
    assert request.context["key"] == "value"
