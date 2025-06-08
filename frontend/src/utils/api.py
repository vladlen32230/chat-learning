import os

import requests
import streamlit as st

# Configuration
API_BASE_URL = os.getenv("BACKEND_URL")
STATIC_FILES_URL = os.getenv("STATIC_FILES_URL")


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


def make_static_request(method: str, path: str, **kwargs) -> requests.Response:
    """Make request to the static file server"""
    url = f"{STATIC_FILES_URL}/{path}"
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Could not connect to the static file server. Make sure the static server is running on port 5015."
        )
        st.stop()
        # This line will never be reached due to st.stop(), but satisfies mypy
        raise


def get_static_file_path(document_id: int, chunk_id: int, chunk_type: str) -> str:
    """Get static file path for API requests"""
    if chunk_type == "image":
        return f"{document_id}/{chunk_id}.jpg"
    else:
        return f"{document_id}/{chunk_id}.txt"


def get_chunk_text_content(document_id: int, chunk_id: int) -> str:
    """Get text chunk content from static file server"""
    file_path = get_static_file_path(document_id, chunk_id, "text")
    try:
        response = make_static_request("GET", file_path)
        if response.status_code == 200:
            return response.text
        else:
            return ""
    except Exception:
        return ""


def get_chunk_image_path(document_id: int, chunk_id: int) -> str:
    """Get image chunk URL from static file server"""
    file_path = get_static_file_path(document_id, chunk_id, "image")
    try:
        response = make_static_request("GET", file_path)
        if response.status_code == 200:
            return f"{STATIC_FILES_URL}/{file_path}"
        else:
            return ""
    except Exception:
        return ""
