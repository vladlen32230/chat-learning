from typing import Literal

from mistralai import Mistral
from mistralai.models.ocrresponse import OCRResponse
from src.config_settings import MISTRAL_API_KEY
from src.helpers.converting import convert_file_to_base64

client = Mistral(api_key=MISTRAL_API_KEY)


async def process_ocr(file: bytes, file_type: Literal["jpg", "pdf"]) -> OCRResponse:
    if file_type == "jpg":
        type = "image_url"
        url = convert_file_to_base64(file, "image/jpeg")
    else:
        type = "document_url"
        url = convert_file_to_base64(file, "application/pdf")

    ocr_response = await client.ocr.process_async(
        model="mistral-ocr-latest",
        document={"type": type, "image_url": url},
        include_image_base64=True,
    )

    return ocr_response
