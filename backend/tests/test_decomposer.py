import pytest
from app.services.decomposer import DecomposerService
from app.schemas.decomposer import TaskGraph, TaskStatus

@pytest.mark.asyncio
async def test_decompose_query(mock_decomposer_service):
    """Test query decomposition"""
    query = "Test query"
    result = await mock_decomposer_service.decompose_query(query)
    
    # Test response structure
    assert isinstance(result, TaskGraph)
    assert result.query == query
    assert len(result.tasks) == 2  # Based on our mock response
    
    # Test task properties (not testing content)
    task1, task2 = result.tasks
    assert task1.status == TaskStatus.PENDING
    assert task2.status == TaskStatus.PENDING
    assert 1 <= task1.estimated_complexity <= 5
    assert 1 <= task2.estimated_complexity <= 5
    
    # Test dependencies
    assert not task1.dependencies  # First task has no dependencies
    assert len(task2.dependencies) == 1  # Second task depends on first task

@pytest.mark.asyncio
async def test_decompose_query_with_context(mock_decomposer_service):
    """Test query decomposition with context"""
    query = "Test query"
    context = {"additional": "context"}
    result = await mock_decomposer_service.decompose_query(query, context)
    
    assert isinstance(result, TaskGraph)
    assert result.query == query

@pytest.mark.asyncio
async def test_decompose_query_error_handling(mock_decomposer_service, mocker):
    """Test error handling during decomposition"""
    # Make the mock client raise an exception
    mock_decomposer_service.client.chat.completions.create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        await mock_decomposer_service.decompose_query("Test query")
