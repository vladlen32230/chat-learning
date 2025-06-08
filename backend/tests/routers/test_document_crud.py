import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session, SQLModel, create_engine, select
from src.db_models import Chunk, Document

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

    # Override the get_session dependency
    with patch("src.routers.document_crud.get_session", get_test_session):
        yield TestClient(app)

    SQLModel.metadata.drop_all(test_engine)


def create_mock_httpx_response(status_code=200):
    """Helper function to create mock httpx response"""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = MagicMock()
    if status_code >= 400:
        from httpx import HTTPStatusError

        mock_response.raise_for_status.side_effect = HTTPStatusError(
            message=f"HTTP {status_code}", request=MagicMock(), response=mock_response
        )
    return mock_response


def test_get_documents_empty(client):
    """Test getting documents when database is empty"""
    response = client.get("/document")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_documents_with_data(client):
    """Test getting documents when database has data"""
    # Create test documents
    with get_test_session() as session:
        doc1 = Document(name="Document 1")
        doc2 = Document(name="Document 2")
        session.add(doc1)
        session.add(doc2)
        session.flush()

    response = client.get("/document")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Verify both documents are returned
    names = [doc["name"] for doc in data]
    assert "Document 1" in names
    assert "Document 2" in names


def test_get_document_success(client):
    """Test successful document retrieval with chunks"""
    # Create test document and chunks
    with get_test_session() as session:
        document = Document(name="Test Document")
        session.add(document)
        session.flush()

        chunk1 = Chunk(type="text", document_id=document.id, completed=False)
        chunk2 = Chunk(type="image", document_id=document.id, completed=True)
        session.add(chunk1)
        session.add(chunk2)
        session.flush()

        document_id = document.id

    response = client.get(f"/document/{document_id}/full")

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["name"] == "Test Document"
    assert data["document"]["id"] == document_id
    assert len(data["chunks"]) == 2

    # Verify chunks
    chunk_types = [chunk["type"] for chunk in data["chunks"]]
    assert "text" in chunk_types
    assert "image" in chunk_types


def test_get_document_not_found(client):
    """Test getting non-existent document"""
    response = client.get("/document/999/full")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Document not found"


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_success_pdf(mock_chunk_text, mock_process_ocr, client):
    """Test successful document creation with PDF file"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text from PDF"
    mock_chunk_text.return_value = ["Chunk 1", "Chunk 2"]

    # Create fake PDF file
    pdf_content = b"fake pdf content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "Test PDF Document"},
            files=[("files", ("test.pdf", pdf_content, "application/pdf"))],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test PDF Document"
        assert "id" in data

        # Verify httpx client was called for file uploads
        assert mock_client_instance.post.call_count == 2  # Two chunks uploaded

    # Verify database entries
    with get_test_session() as session:
        document = session.get(Document, data["id"])
        assert document is not None
        assert document.name == "Test PDF Document"


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_success_images(mock_chunk_text, mock_process_ocr, client):
    """Test successful document creation with image files"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text from image"
    mock_chunk_text.return_value = [
        "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    ]

    # Create fake image files
    image_content = b"fake image content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "Test Image Document"},
            files=[
                ("files", ("test1.jpg", image_content, "image/jpeg")),
                ("files", ("test2.png", image_content, "image/png")),
            ],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Image Document"
        assert "id" in data

        # Verify httpx client was called for file upload
        mock_client_instance.post.assert_called()


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_mixed_files(mock_chunk_text, mock_process_ocr, client):
    """Test document creation with mixed PDF and image files"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = [
        "Text chunk",
        "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
    ]

    pdf_content = b"fake pdf content"
    image_content = b"fake image content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "Mixed Document"},
            files=[
                ("files", ("test.pdf", pdf_content, "application/pdf")),
                ("files", ("test.jpg", image_content, "image/jpeg")),
            ],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mixed Document"

        # Verify httpx client was called for file uploads
        mock_client_instance.post.assert_called()


def test_create_document_invalid_file_type(client):
    """Test document creation with invalid file type"""
    invalid_content = b"invalid file content"

    response = client.post(
        "/document",
        data={"name": "Invalid Document"},
        files=[("files", ("test.txt", invalid_content, "text/plain"))],
    )

    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file type" in data["detail"]


def test_create_document_no_valid_files(client):
    """Test document creation with no valid files"""
    response = client.post("/document", data={"name": "No Files Document"}, files=[])

    assert (
        response.status_code == 422
    )  # FastAPI validation error for missing required field


def test_delete_document_success(client):
    """Test successful document deletion"""
    # Create test document and chunks
    with get_test_session() as session:
        document = Document(name="To Delete")
        session.add(document)
        session.flush()

        chunk1 = Chunk(type="text", document_id=document.id, completed=False)
        chunk2 = Chunk(type="image", document_id=document.id, completed=True)
        session.add(chunk1)
        session.add(chunk2)
        session.flush()

        document_id = document.id
        chunk1_id = chunk1.id
        chunk2_id = chunk2.id

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.delete.return_value = create_mock_httpx_response(204)

        response = client.delete(f"/document/{document_id}")

        assert response.status_code == 204

        # Verify httpx client was called for file deletions
        assert mock_client_instance.delete.call_count == 2  # Two chunks deleted

    # Verify document and chunks are deleted from database
    with get_test_session() as session:
        document = session.get(Document, document_id)
        assert document is None

        chunk1 = session.get(Chunk, chunk1_id)
        assert chunk1 is None

        chunk2 = session.get(Chunk, chunk2_id)
        assert chunk2 is None


def test_delete_document_not_found(client):
    """Test deleting non-existent document"""
    response = client.delete("/document/999")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Document not found"


def test_update_chunk_success(client):
    """Test successful chunk update"""
    # Create test document and chunk
    with get_test_session() as session:
        document = Document(name="Test Document")
        session.add(document)
        session.flush()

        chunk = Chunk(type="text", document_id=document.id, completed=False)
        session.add(chunk)
        session.flush()

        document_id = document.id
        chunk_id = chunk.id

    response = client.put(
        f"/document/{document_id}/chunk/{chunk_id}", json={"completed": True}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["id"] == chunk_id

    # Verify database update
    with get_test_session() as session:
        chunk = session.get(Chunk, chunk_id)
        assert chunk.completed is True


def test_update_chunk_document_not_found(client):
    """Test updating chunk when document doesn't exist"""
    response = client.put("/document/999/chunk/1", json={"completed": True})

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Document not found"


def test_update_chunk_chunk_not_found(client):
    """Test updating non-existent chunk"""
    # Create test document
    with get_test_session() as session:
        document = Document(name="Test Document")
        session.add(document)
        session.flush()
        document_id = document.id

    response = client.put(
        f"/document/{document_id}/chunk/999", json={"completed": True}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Chunk not found"


def test_update_chunk_wrong_document(client):
    """Test updating chunk that belongs to different document"""
    # Create test documents and chunk
    with get_test_session() as session:
        document1 = Document(name="Document 1")
        document2 = Document(name="Document 2")
        session.add(document1)
        session.add(document2)
        session.flush()

        chunk = Chunk(type="text", document_id=document1.id, completed=False)
        session.add(chunk)
        session.flush()

        document2_id = document2.id
        chunk_id = chunk.id

    response = client.put(
        f"/document/{document2_id}/chunk/{chunk_id}", json={"completed": True}
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Chunk not found"


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_with_image_chunks(mock_chunk_text, mock_process_ocr, client):
    """Test successful document creation that results in image chunks being saved"""
    # Mock OCR and chunking responses with base64 images
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = [
        "Regular text chunk",
        "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        "Another text chunk",
    ]

    # Create fake PDF file
    pdf_content = b"fake pdf content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "Test Document with Images"},
            files=[("files", ("test.pdf", pdf_content, "application/pdf"))],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Document with Images"

        # Verify httpx client was called for file uploads
        assert mock_client_instance.post.call_count == 3  # 3 chunks uploaded

    # Verify that both text and image chunks were created
    with get_test_session() as session:
        document_id = data["id"]
        chunks = session.exec(
            select(Chunk).where(Chunk.document_id == document_id)
        ).all()

        # Should have 3 chunks: 2 text chunks and 1 image chunk
        assert len(chunks) == 3
        chunk_types = [chunk.type for chunk in chunks]
        assert "text" in chunk_types
        assert "image" in chunk_types


def test_delete_document_with_static_server_error(client):
    """Test deleting document when static server returns error"""
    # Create test document and chunks
    with get_test_session() as session:
        document = Document(name="Server Error Test")
        session.add(document)
        session.flush()

        chunk = Chunk(type="text", document_id=document.id, completed=False)
        session.add(chunk)
        session.flush()

        document_id = document.id

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock to simulate server error but don't raise exception
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        # Create a response that returns 500 but doesn't raise when raise_for_status is called
        # because the code handles non-404 errors gracefully
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.return_value = None  # Don't raise
        mock_client_instance.delete.return_value = mock_response

        response = client.delete(f"/document/{document_id}")

        # Should still succeed even if static server has errors
        assert response.status_code == 204

    # Verify document is deleted from database
    with get_test_session() as session:
        document = session.get(Document, document_id)
        assert document is None


def test_delete_document_with_network_error(client):
    """Test deleting document when static server is unreachable"""
    # Create test document and chunks
    with get_test_session() as session:
        document = Document(name="Network Error Test")
        session.add(document)
        session.flush()

        chunk = Chunk(type="text", document_id=document.id, completed=False)
        session.add(chunk)
        session.flush()

        document_id = document.id

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock to simulate network error
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        from httpx import RequestError

        mock_client_instance.delete.side_effect = RequestError("Network error")

        response = client.delete(f"/document/{document_id}")

        # Should still succeed even if static server is unreachable
        assert response.status_code == 204

    # Verify document is deleted from database
    with get_test_session() as session:
        document = session.get(Document, document_id)
        assert document is None


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_mixed_valid_invalid_files(
    mock_chunk_text, mock_process_ocr, client
):
    """Test document creation with mix of valid and invalid files"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = ["Text chunk"]

    pdf_content = b"fake pdf content"
    invalid_content = b"invalid file content"

    response = client.post(
        "/document",
        data={"name": "Mixed Valid Invalid"},
        files=[
            ("files", ("test.pdf", pdf_content, "application/pdf")),
            ("files", ("test.txt", invalid_content, "text/plain")),
        ],
    )

    # Should fail because of invalid file
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file type" in data["detail"]


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_filename_based_validation(
    mock_chunk_text, mock_process_ocr, client
):
    """Test file validation based on filename when content_type is missing"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = ["Text chunk"]

    pdf_content = b"fake pdf content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        # Test PDF file validation by filename
        response = client.post(
            "/document",
            data={"name": "Filename Validation"},
            files=[("files", ("test.pdf", pdf_content, None))],  # No content_type
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Filename Validation"


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_actual_image_processing(
    mock_chunk_text, mock_process_ocr, client
):
    """Test actual image chunk processing and file uploading"""
    # Mock responses that include both text and base64 image chunks
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = [
        "Text chunk 1",
        "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        "Text chunk 2",
    ]

    pdf_content = b"fake pdf content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "Image Processing Test"},
            files=[("files", ("test.pdf", pdf_content, "application/pdf"))],
        )

        assert response.status_code == 201
        data = response.json()

        # Verify httpx client was called for file uploads
        assert mock_client_instance.post.call_count == 3  # 3 chunks uploaded

    # Verify chunks were created with correct types
    with get_test_session() as session:
        document_id = data["id"]
        chunks = session.exec(
            select(Chunk).where(Chunk.document_id == document_id)
        ).all()

        assert len(chunks) == 3

        # Check that we have both text and image chunks
        text_chunks = [c for c in chunks if c.type == "text"]
        image_chunks = [c for c in chunks if c.type == "image"]

        assert len(text_chunks) == 2
        assert len(image_chunks) == 1

        # Verify image chunk processing
        image_chunk = image_chunks[0]
        assert image_chunk.type == "image"
        assert image_chunk.completed is False


@patch("src.routers.document_crud.process_ocr")
@patch("src.routers.document_crud.chunk_text")
def test_create_document_jpeg_extension_validation(
    mock_chunk_text, mock_process_ocr, client
):
    """Test additional file extension validation paths"""
    # Mock OCR and chunking responses
    mock_process_ocr.return_value = "Extracted text"
    mock_chunk_text.return_value = ["Text chunk"]

    # Test .jpeg extension (different from .jpg)
    image_content = b"fake image content"

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = create_mock_httpx_response(200)

        response = client.post(
            "/document",
            data={"name": "JPEG Extension Test"},
            files=[("files", ("test.jpeg", image_content, "image/jpeg"))],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "JPEG Extension Test"


def test_create_document_only_empty_files(client):
    """Test when no files are provided"""
    # Empty files list should trigger validation error
    response = client.post(
        "/document",
        data={"name": "Only Invalid Files"},
        files=[],  # Empty files list
    )

    # This should trigger FastAPI validation error
    assert response.status_code == 422


def test_update_chunk_set_to_false(client):
    """Test updating chunk completed status to False"""
    # Create test document and chunk
    with get_test_session() as session:
        document = Document(name="Test Document")
        session.add(document)
        session.flush()

        chunk = Chunk(type="text", document_id=document.id, completed=True)
        session.add(chunk)
        session.flush()

        document_id = document.id
        chunk_id = chunk.id

    response = client.put(
        f"/document/{document_id}/chunk/{chunk_id}", json={"completed": False}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is False
    assert data["id"] == chunk_id


def test_delete_document_file_not_found_on_server(client):
    """Test deleting document when files don't exist on static server (404)"""
    # Create test document and chunks
    with get_test_session() as session:
        document = Document(name="Files Not Found")
        session.add(document)
        session.flush()

        chunk = Chunk(type="text", document_id=document.id, completed=False)
        session.add(chunk)
        session.flush()

        document_id = document.id

    with patch("httpx.AsyncClient") as mock_httpx_client:
        # Setup httpx mock to return 404 for file deletions
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.delete.return_value = create_mock_httpx_response(404)

        response = client.delete(f"/document/{document_id}")

        # Should succeed even if files don't exist on server (404 is acceptable)
        assert response.status_code == 204

    # Verify document is deleted from database
    with get_test_session() as session:
        document = session.get(Document, document_id)
        assert document is None
