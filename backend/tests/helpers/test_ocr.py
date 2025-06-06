from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai.models.ocrresponse import OCRResponse
from src.helpers.ocr import process_ocr


@pytest.mark.asyncio
@patch("src.helpers.ocr.client")
@patch("src.helpers.ocr.convert_file_to_base64")
async def test_process_ocr_jpg(mock_convert, mock_client):
    # Arrange
    mock_file = b"fake_jpg_data"
    mock_url = "data:image/jpeg;base64,fake_data"
    mock_convert.return_value = mock_url

    mock_response = MagicMock(spec=OCRResponse)
    mock_client.ocr.process_async = AsyncMock(return_value=mock_response)

    # Act
    result = await process_ocr(mock_file, "jpg")

    # Assert
    mock_convert.assert_called_once_with(mock_file, "image/jpeg")
    mock_client.ocr.process_async.assert_called_once_with(
        model="mistral-ocr-latest",
        document={"type": "image_url", "image_url": mock_url},
        include_image_base64=True,
    )
    assert result == mock_response


@pytest.mark.asyncio
@patch("src.helpers.ocr.client")
@patch("src.helpers.ocr.convert_file_to_base64")
async def test_process_ocr_pdf(mock_convert, mock_client):
    # Arrange
    mock_file = b"fake_pdf_data"
    mock_url = "data:application/pdf;base64,fake_data"
    mock_convert.return_value = mock_url

    mock_response = MagicMock(spec=OCRResponse)
    mock_client.ocr.process_async = AsyncMock(return_value=mock_response)

    # Act
    result = await process_ocr(mock_file, "pdf")

    # Assert
    mock_convert.assert_called_once_with(mock_file, "application/pdf")
    mock_client.ocr.process_async.assert_called_once_with(
        model="mistral-ocr-latest",
        document={"type": "document_url", "image_url": mock_url},
        include_image_base64=True,
    )
    assert result == mock_response
