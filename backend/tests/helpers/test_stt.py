from unittest.mock import MagicMock, patch

import pytest
from src.helpers.stt import transcribe


@patch("src.helpers.stt.client")
def test_transcribe(mock_client):
    # Arrange
    mock_audio_file = b"fake_audio_data"
    mock_text = "This is a transcribed text"

    mock_transcript = MagicMock()
    mock_transcript.text = mock_text
    mock_client.audio.transcriptions.create.return_value = mock_transcript

    # Act
    result = transcribe(mock_audio_file)

    # Assert
    mock_client.audio.transcriptions.create.assert_called_once_with(
        model="openai/whisper-large-v3", file=mock_audio_file
    )
    assert result == mock_text
