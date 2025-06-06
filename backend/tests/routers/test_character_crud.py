import os
from contextlib import contextmanager
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session, SQLModel, create_engine
from src.db_models import Character

# Define test engine with proper SQLite configuration for testing
test_engine = create_engine(
    "sqlite:///test.db", connect_args={"check_same_thread": True}
)


@contextmanager
def get_test_session() -> Generator[Session, None, None]:
    """Test session that uses in-memory SQLite database"""
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
    with patch("src.database_con.get_session", get_test_session):
        yield TestClient(app)

    SQLModel.metadata.drop_all(test_engine)


def test_create_character_success(client):
    """Test successful character creation"""
    response = client.post(
        "/character",
        json={
            "name": "Test Character",
            "prompt_description": "A test character description",
            "voice_name": "af_bella",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Character"
    assert data["prompt_description"] == "A test character description"
    assert data["voice_name"] == "af_bella"
    assert "id" in data

    # Verify database entry
    with Session(test_engine) as session:
        character = session.get(Character, data["id"])
        assert character is not None
        assert character.name == "Test Character"
        assert character.prompt_description == "A test character description"
        assert character.voice_name == "af_bella"


def test_create_character_without_voice_name(client):
    """Test character creation without voice_name (optional field)"""
    response = client.post(
        "/character",
        json={
            "name": "No Voice Character",
            "prompt_description": "Character without voice",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "No Voice Character"
    assert data["prompt_description"] == "Character without voice"
    assert data["voice_name"] is None

    # Verify database entry
    with get_test_session() as session:
        character = session.get(Character, data["id"])
        assert character is not None
        assert character.voice_name is None


def test_get_characters_empty(client):
    """Test getting characters when database is empty"""
    response = client.get("/character")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_characters_with_data(client):
    """Test getting characters when database has data"""
    # Create test characters
    client.post(
        "/character",
        json={
            "name": "Character 1",
            "prompt_description": "First character",
            "voice_name": "af_nicole",
        },
    )
    client.post(
        "/character",
        json={"name": "Character 2", "prompt_description": "Second character"},
    )

    # Get all characters
    response = client.get("/character")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Verify both characters are returned
    names = [char["name"] for char in data]
    assert "Character 1" in names
    assert "Character 2" in names


def test_delete_character_success(client):
    """Test successful character deletion"""
    # Create a character first
    create_response = client.post(
        "/character",
        json={"name": "To Delete", "prompt_description": "Character to be deleted"},
    )
    character_id = create_response.json()["id"]

    # Delete the character
    response = client.delete(f"/character/{character_id}")

    assert response.status_code == 204

    # Verify character is deleted from database
    with get_test_session() as session:
        character = session.get(Character, character_id)
        assert character is None


def test_delete_character_not_found(client):
    """Test deleting non-existent character"""
    response = client.delete("/character/999")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Character not found"
