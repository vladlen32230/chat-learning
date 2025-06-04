from openai import AsyncOpenAI
import os
from mistralai.models.ocrresponse import OCRResponse
import asyncio

async def chunk_text(ocr_response: OCRResponse) -> list[str]:
    client = AsyncOpenAI(
        api_key=os.environ['OPENROUTER_API_KEY'],
        base_url="https://openrouter.ai/api/v1"
    )

    system_prompt = (
        "You are a helpful assistant that will parse given text into logical chunks. "
        "Every word should not be lost and should be in output list. "
        "Output ONLY a Python-style list of strings, where each string is one logical chunk "
        "that a student can learn independently. If you see like \"![img-0.jpeg](img-0.jpeg)\", "
        "it should be treated as separate chunk."
    )

    requests = []

    for page in ocr_response.pages:
        requests.append(client.chat.completions.create(
            model="qwen/qwen-2.5-72b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": page.markdown
                }
            ]
        ))

    responses = await asyncio.gather(*requests)

    return [response.choices[0].message.content for response in responses]
