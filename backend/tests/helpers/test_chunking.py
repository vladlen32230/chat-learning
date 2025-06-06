from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai.models.ocrresponse import OCRResponse
from src.helpers.chunking import chunk_text


@pytest.mark.asyncio
@patch("src.helpers.chunking.asyncio.gather")
@patch("src.helpers.chunking.client")
@patch("src.helpers.chunking.loads")
async def test_chunk_text_with_text_only(mock_loads, mock_client, mock_gather):
    # Arrange
    mock_page1 = MagicMock()
    mock_page1.markdown = "This is page 1 content"
    mock_page1.images = []

    mock_page2 = MagicMock()
    mock_page2.markdown = "This is page 2 content"
    mock_page2.images = []

    mock_ocr_response = MagicMock(spec=OCRResponse)
    mock_ocr_response.pages = [mock_page1, mock_page2]

    mock_response1 = MagicMock()
    mock_response1.choices[0].message.content = '["Chunk 1", "Chunk 2"]'

    mock_response2 = MagicMock()
    mock_response2.choices[0].message.content = '["Chunk 3", "Chunk 4"]'

    # Mock asyncio.gather to be awaitable and return the responses
    mock_gather = AsyncMock(return_value=[mock_response1, mock_response2])
    mock_loads.side_effect = [["Chunk 1", "Chunk 2"], ["Chunk 3", "Chunk 4"]]

    # Mock the client create method
    mock_async_create = AsyncMock()
    mock_client.chat.completions.create = mock_async_create

    # Act
    with patch("src.helpers.chunking.asyncio.gather", mock_gather):
        result = await chunk_text(mock_ocr_response)

    # Assert
    assert mock_client.chat.completions.create.call_count == 2
    assert mock_loads.call_count == 2
    assert result == ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4"]


@pytest.mark.asyncio
@patch("src.helpers.chunking.asyncio.gather")
@patch("src.helpers.chunking.client")
@patch("src.helpers.chunking.loads")
@patch("src.helpers.chunking.re.findall")
async def test_chunk_text_with_images(
    mock_findall, mock_loads, mock_client, mock_gather
):
    # Arrange
    mock_image = MagicMock()
    mock_image.image_base64 = "base64_image_data"

    mock_page = MagicMock()
    mock_page.markdown = "Page with image content"
    mock_page.images = [mock_image]

    mock_ocr_response = MagicMock(spec=OCRResponse)
    mock_ocr_response.pages = [mock_page]

    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = '["Text chunk", "![img-0.jpeg](img-0.jpeg)"]'

    mock_gather = AsyncMock(return_value=[mock_response])
    mock_loads.return_value = ["Text chunk", "![img-0.jpeg](img-0.jpeg)"]

    # Mock re.findall to return image IDs for the second chunk only
    def findall_side_effect(pattern, text):
        if "![img-0.jpeg](img-0.jpeg)" in text:
            return ["0"]
        return []

    mock_findall.side_effect = findall_side_effect
    mock_client.chat.completions.create = AsyncMock()

    # Act
    with patch("src.helpers.chunking.asyncio.gather", mock_gather):
        result = await chunk_text(mock_ocr_response)

    # Assert
    assert mock_client.chat.completions.create.call_count == 1
    assert mock_loads.call_count == 1
    assert result == ["Text chunk", "base64_image_data"]
