from unittest.mock import patch

import pytest
from src.helpers.converting import convert_file_to_base64


@patch("src.helpers.converting.base64.b64encode")
def test_convert_file_to_base64(mock_b64encode):
    # Arrange
    mock_file = b"test file content"
    mock_file_type = "image/jpeg"
    mock_encoded = b"dGVzdCBmaWxlIGNvbnRlbnQ="  # base64 of "test file content"
    mock_b64encode.return_value = mock_encoded

    # Act
    result = convert_file_to_base64(mock_file, mock_file_type)

    # Assert
    mock_b64encode.assert_called_once_with(mock_file)
    expected = f"data:{mock_file_type};base64,{mock_encoded.decode('utf-8')}"
    assert result == expected


def test_convert_file_to_base64_integration():
    # Arrange
    mock_file = b"test"
    mock_file_type = "application/pdf"

    # Act
    result = convert_file_to_base64(mock_file, mock_file_type)

    # Assert
    assert result.startswith(f"data:{mock_file_type};base64,")
    assert "dGVzdA==" in result  # base64 encoding of "test"
