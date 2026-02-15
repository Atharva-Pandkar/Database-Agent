import pytest
from typing import Dict, Any
from unittest.mock import patch
from app.core.config import Settings, get_settings
from app.services.decomposer import DecomposerService

class MockSettings(Settings):
    openai_api_key: str = "test-key"
    openai_model: str = "test-model"

    class Config:
        env_file = None

@pytest.fixture(autouse=True)
def mock_settings():
    """Automatically mock settings for all tests"""
    with patch('app.core.config.get_settings', return_value=MockSettings()):
        yield

@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock response from OpenAI API"""
    return {
        "choices": [
            {
                "message": {
                    "content": {
                        "tasks": [
                            {
                                "title": "Task 1",
                                "description": "Description 1",
                                "dependencies": [],
                                "complexity": 2
                            },
                            {
                                "title": "Task 2",
                                "description": "Description 2",
                                "dependencies": ["Task 1"],
                                "complexity": 3
                            }
                        ]
                    }
                }
            }
        ]
    }

@pytest.fixture
def mock_decomposer_service(mocker, mock_openai_response):
    """Create a DecomposerService with mocked OpenAI client"""
    # Mock the settings first
    settings = MockSettings()
    
    service = DecomposerService()
    service.settings = settings
    
    # Mock the OpenAI client
    mock_client = mocker.MagicMock()
    mock_completion = mocker.AsyncMock()
    mock_completion.return_value.choices[0].message.content = mock_openai_response["choices"][0]["message"]["content"]
    mock_client.chat.completions.create = mock_completion
    
    service.client = mock_client
    return service