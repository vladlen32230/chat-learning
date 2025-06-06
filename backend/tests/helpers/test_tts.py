from unittest.mock import MagicMock, patch

import pytest
from src.helpers.tts import generate_speech


@pytest.mark.asyncio
@patch("src.helpers.tts.client")
async def test_generate_speech_default_format(mock_client):
    # Arrange
    mock_text = "Hello world"
    mock_voice = "test_voice"
    mock_content = b"fake_audio_content"

    mock_response = MagicMock()
    mock_response.content = mock_content
    mock_client.audio.speech.create.return_value = mock_response

    # Act
    result = await generate_speech(mock_text, mock_voice)

    # Assert
    mock_client.audio.speech.create.assert_called_once_with(
        model="hexgrad/Kokoro-82M",
        voice=mock_voice,
        input=mock_text,
        response_format="mp3",
    )
    assert result == mock_content


@pytest.mark.asyncio
@patch("src.helpers.tts.client")
async def test_generate_speech_custom_format(mock_client):
    # Arrange
    mock_text = "Hello world"
    mock_voice = "test_voice"
    mock_format = "wav"
    mock_content = b"fake_audio_content"

    mock_response = MagicMock()
    mock_response.content = mock_content
    mock_client.audio.speech.create.return_value = mock_response

    # Act
    result = await generate_speech(mock_text, mock_voice, mock_format)

    # Assert
    mock_client.audio.speech.create.assert_called_once_with(
        model="hexgrad/Kokoro-82M",
        voice=mock_voice,
        input=mock_text,
        response_format=mock_format,
    )
    assert result == mock_content
