from pathlib import Path

import requests
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8015"  # Backend API port


def make_api_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make API request to the backend"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Could not connect to the backend API. Make sure the FastAPI server is running on port 8015."
        )
        st.stop()
        # This line will never be reached due to st.stop(), but satisfies mypy
        raise


def get_static_file_path(document_id: int, chunk_id: int, chunk_type: str) -> Path:
    """Get local static file path"""
    # Get the path to the static folder relative to the frontend directory
    static_dir = Path("../static")

    if chunk_type == "image":
        return static_dir / str(document_id) / f"{chunk_id}.jpg"
    else:
        return static_dir / str(document_id) / f"{chunk_id}.txt"


def get_chunk_text_content(document_id: int, chunk_id: int) -> str:
    """Get text chunk content from local static folder"""
    file_path = get_static_file_path(document_id, chunk_id, "text")
    try:
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        else:
            return ""
    except Exception:
        return ""


def get_chunk_image_path(document_id: int, chunk_id: int) -> str:
    """Get image chunk path from local static folder"""
    file_path = get_static_file_path(document_id, chunk_id, "image")
    if file_path.exists():
        return str(file_path)
    else:
        return ""
