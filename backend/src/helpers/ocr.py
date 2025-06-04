from mistralai import Mistral
from mistralai.models.ocrresponse import OCRResponse
import os
from src.helpers.other import convert_file_to_base64
from typing import Literal

async def process_ocr(file: bytes, file_type: Literal['jpg', 'pdf']) -> OCRResponse:
    client = Mistral(api_key=os.environ['MISTRAL_API_KEY'])

    if file_type == 'jpg':
        type = 'image_url'
        url = convert_file_to_base64(file, 'image/jpeg')
    else:
        type = 'document_url'
        url = convert_file_to_base64(file, 'application/pdf')

    ocr_response = await client.ocr.process_async(
        model="mistral-ocr-latest",
        document={
            "type": type,
            "image_url": url
        },
        include_image_base64=True
    )

    return ocr_response