import json
import os
from contextlib import contextmanager
from typing import Generator
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session, SQLModel, create_engine
from src.db_models import Character, Chunk, Document

# Define test engine with proper SQLite configuration for testing
test_engine = create_engine(
    "sqlite:///test.db", connect_args={"check_same_thread": False}
)


@contextmanager
def get_test_session() -> Generator[Session, None, None]:
    """Test session that uses SQLite database"""
    session = Session(test_engine)
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    else:
        session.commit()
    finally:
        session.close()


@pytest.fixture
def client():
    """Create test client with overridden database session"""
    SQLModel.metadata.create_all(test_engine)
    # Override the get_session dependency with correct patch target
    with patch("src.routers.chat_interaction.get_session", get_test_session):
        yield TestClient(app)

    SQLModel.metadata.drop_all(test_engine)
    # Clean up test database file
    if os.path.exists("test_chat.db"):
        os.remove("test_chat.db")


@pytest.fixture
def setup_test_data():
    """Setup test data in database"""
    with get_test_session() as session:
        # Create test character
        character = Character(
            id=1,
            name="Test Character",
            prompt_description="A test character",
            voice_name="af_bella",
        )
        session.add(character)

        # Create test character without voice
        character_no_voice = Character(
            id=2,
            name="No Voice Character",
            prompt_description="Character without voice",
            voice_name=None,
        )
        session.add(character_no_voice)

        # Create test document
        document = Document(id=1, name="Test Document")
        session.add(document)

        # Create test text chunk
        text_chunk = Chunk(id=1, type="text", document_id=1, completed=True)
        session.add(text_chunk)

        # Create test image chunk
        image_chunk = Chunk(id=2, type="image", document_id=1, completed=True)
        session.add(image_chunk)

        session.commit()

        # Return test data IDs
        return {
            "character_id": 1,
            "character_no_voice_id": 2,
            "document_id": 1,
            "text_chunk_id": 1,
            "image_chunk_id": 2,
        }


@patch("src.routers.chat_interaction.chat_with_llm")
@patch("src.routers.chat_interaction.generate_speech")
@patch("src.routers.chat_interaction.convert_file_to_base64")
@patch("builtins.open", new_callable=mock_open, read_data="Test chunk content")
@patch("pathlib.Path.exists")
def test_chat_text_chunk_with_voice_success(
    mock_exists, mock_file, mock_convert, mock_speech, mock_llm, client, setup_test_data
):
    """Test successful chat with text chunk and character with voice"""
    test_data = setup_test_data

    # Setup mocks
    mock_exists.return_value = True
    mock_llm.return_value = "Test response from LLM"
    mock_speech.return_value = b"mock_speech_bytes"
    mock_convert.return_value = "base64_encoded_speech"

    messages_history = json.dumps(
        [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]
    )

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello, tell me about this content",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test response from LLM"
    assert data["speech"] == "base64_encoded_speech"
    assert data["input_user_text"] == "Hello, tell me about this content"

    # Verify LLM was called with correct messages
    mock_llm.assert_called_once()
    mock_speech.assert_called_once_with("Test response from LLM", "af_bella")


@patch("src.routers.chat_interaction.chat_with_llm")
@patch("src.routers.chat_interaction.convert_file_to_base64")
@patch("builtins.open", new_callable=mock_open, read_data=b"mock_image_bytes")
@patch("pathlib.Path.exists")
def test_chat_image_chunk_without_voice_success(
    mock_exists, mock_file, mock_convert, mock_llm, client, setup_test_data
):
    """Test successful chat with image chunk and character without voice"""
    test_data = setup_test_data

    # Setup mocks
    mock_exists.return_value = True
    mock_llm.return_value = "Test response about image"
    mock_convert.return_value = "base64_encoded_image"

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['image_chunk_id']}",
        data={
            "character_id": test_data["character_no_voice_id"],
            "messages_history": messages_history,
            "new_message_text": "What do you see in this image?",
            "model": "google/gemini-2.5-pro-preview",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Test response about image"
    assert data["speech"] is None  # No voice for this character
    assert data["input_user_text"] == "What do you see in this image?"


@patch("src.routers.chat_interaction.chat_with_llm")
@patch("src.routers.chat_interaction.transcribe")
@patch("builtins.open", new_callable=mock_open, read_data="Test content")
@patch("pathlib.Path.exists")
def test_chat_with_speech_input(
    mock_exists, mock_file, mock_transcribe, mock_llm, client, setup_test_data
):
    """Test chat with speech input (STT)"""
    test_data = setup_test_data

    # Setup mocks
    mock_exists.return_value = True
    mock_transcribe.return_value = "Transcribed text from speech"
    mock_llm.return_value = "Response to transcribed text"

    messages_history = json.dumps([])

    # Create mock audio file
    audio_content = b"mock_audio_data"

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_no_voice_id"],
            "messages_history": messages_history,
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
        files={"new_message_speech": ("audio.mp3", audio_content, "audio/mpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["input_user_text"] == "Transcribed text from speech"
    mock_transcribe.assert_called_once_with(audio_content)


def test_chat_character_not_found(client, setup_test_data):
    """Test chat with non-existent character"""
    test_data = setup_test_data

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": 999,  # Non-existent character
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Character not found"


def test_chat_document_not_found(client, setup_test_data):
    """Test chat with non-existent document"""
    test_data = setup_test_data

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/999/chunk/{test_data['text_chunk_id']}",  # Non-existent document
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_chat_chunk_not_found(client, setup_test_data):
    """Test chat with non-existent chunk"""
    test_data = setup_test_data

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/999",  # Non-existent chunk
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk not found"


def test_chat_chunk_wrong_document(client, setup_test_data):
    """Test chat with chunk that doesn't belong to the document"""
    test_data = setup_test_data

    # Create another document and chunk
    with get_test_session() as session:
        other_document = Document(id=2, name="Other Document")
        session.add(other_document)
        other_chunk = Chunk(id=3, type="text", document_id=2, completed=True)
        session.add(other_chunk)
        session.commit()

    messages_history = json.dumps([])

    # Try to access chunk from wrong document
    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/3",  # Chunk belongs to document 2, not 1
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk not found"


def test_chat_invalid_json_messages_history(client, setup_test_data):
    """Test chat with invalid JSON in messages_history"""
    test_data = setup_test_data

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_id"],
            "messages_history": "invalid json",  # Invalid JSON
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 400
    assert "Invalid JSON format for messages_history" in response.json()["detail"]


def test_chat_invalid_message_format(client, setup_test_data):
    """Test chat with invalid message format in messages_history"""
    test_data = setup_test_data

    # Invalid message format (missing required fields)
    messages_history = json.dumps(
        [{"role": "user"}, {"content": "Hello"}]  # Missing content  # Missing role
    )

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 400
    assert "Invalid message format in messages_history" in response.json()["detail"]


@patch("builtins.open", new_callable=mock_open, read_data="Test content")
@patch("pathlib.Path.exists")
def test_chat_text_chunk_file_not_found(
    mock_exists, mock_file, client, setup_test_data
):
    """Test chat when text chunk file doesn't exist"""
    test_data = setup_test_data

    mock_exists.return_value = False  # File doesn't exist

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk file not found"


@patch("builtins.open", new_callable=mock_open, read_data=b"image data")
@patch("pathlib.Path.exists")
def test_chat_image_chunk_file_not_found(
    mock_exists, mock_file, client, setup_test_data
):
    """Test chat when image chunk file doesn't exist"""
    test_data = setup_test_data

    mock_exists.return_value = False  # File doesn't exist

    messages_history = json.dumps([])

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['image_chunk_id']}",
        data={
            "character_id": test_data["character_id"],
            "messages_history": messages_history,
            "new_message_text": "Hello",
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk file not found"


@patch("src.routers.chat_interaction.chat_with_llm")
@patch("builtins.open", new_callable=mock_open, read_data="Test content")
@patch("pathlib.Path.exists")
def test_chat_without_new_message(
    mock_exists, mock_file, mock_llm, client, setup_test_data
):
    """Test chat without providing new_message_text or new_message_speech"""
    test_data = setup_test_data

    mock_exists.return_value = True
    mock_llm.return_value = "Response without new message"

    messages_history = json.dumps(
        [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]
    )

    response = client.post(
        f"/chat/document/{test_data['document_id']}/chunk/{test_data['text_chunk_id']}",
        data={
            "character_id": test_data["character_no_voice_id"],
            "messages_history": messages_history,
            # No new_message_text or new_message_speech
            "model": "google/gemini-2.5-flash-preview-05-20",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["input_user_text"] is None
    assert data["text"] == "Response without new message"
