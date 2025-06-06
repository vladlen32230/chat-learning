import asyncio
import re
from json import loads

from mistralai.models.ocrresponse import OCRResponse
from openai import AsyncOpenAI
from src.config_settings import OPENROUTER_API_KEY

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1"
)


async def chunk_text(ocr_response: OCRResponse) -> list[str]:
    """
    Chunk is either plain text or base64 encoded image.
    """
    system_prompt = (
        "You are a helpful assistant that will parse given text into logical chunks. "
        "Every word should not be lost and should be in output list. "
        "Output ONLY a Python-style list of strings, where each string is one logical chunk "
        'that a student can learn independently. If you see like "![img-0.jpeg](img-0.jpeg)", '
        "it should be treated as separate chunk. The quotes should be double so it can be parsed using json.loads."
    )

    requests = []

    for page in ocr_response.pages:
        requests.append(
            client.chat.completions.create(
                model="qwen/qwen-2.5-72b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": page.markdown},
                ],
                temperature=0.0,
            )
        )

    responses = await asyncio.gather(*requests)

    chunks_list = [loads(response.choices[0].message.content) for response in responses]

    all_chunks = []

    for page, chunks in zip(ocr_response.pages, chunks_list):
        # Process each chunk to convert image references to base64
        processed_chunks = []
        for chunk in chunks:
            # Look for image markdown pattern: ![img-<id>.jpeg](img-<id>.jpeg)
            img_pattern = r"!\[img-(\d+)\.jpeg\]\(img-\d+\.jpeg\)"
            matches = re.findall(img_pattern, chunk)

            if matches:
                # If this chunk contains image references, replace them with base64 images
                processed_chunk = chunk
                for img_id in matches:
                    img_id = int(img_id)
                    # Replace the markdown image with base64 image
                    img_markdown = f"![img-{img_id}.jpeg](img-{img_id}.jpeg)"
                    base64_image = page.images[img_id].image_base64
                    processed_chunk = processed_chunk.replace(
                        img_markdown, base64_image
                    )
                processed_chunks.append(processed_chunk)
            else:
                # Regular text chunk
                processed_chunks.append(chunk)

        all_chunks.extend(processed_chunks)

    return all_chunks
