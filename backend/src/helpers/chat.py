from openai import AsyncOpenAI
from src.config import OPENROUTER_API_KEY

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

async def chat_with_llm(messages: list[dict], model_name: str) -> str:
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages
    )

    return response.choices[0].message.content