from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.helpers.chat_llm import chat_with_llm


@pytest.mark.asyncio
async def test_chat_with_llm():
    # Arrange
    mock_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    mock_model = "test-model"
    mock_response_content = "This is a test response"

    # Create a mock that behaves like the OpenAI response
    mock_message = MagicMock()
    mock_message.content = mock_response_content

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # Mock the entire module's client
    with patch("src.helpers.chat_llm.client") as mock_client:
        # Create an async mock function
        async def mock_create(*args, **kwargs):
            return mock_response

        mock_client.chat.completions.create = mock_create

        # Act
        result = await chat_with_llm(mock_messages, mock_model)

    # Assert
    assert result == mock_response_content
