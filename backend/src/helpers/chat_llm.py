from openai import AsyncOpenAI
from src.config_settings import OPENROUTER_API_KEY

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1"
)


async def chat_with_llm(messages: list[dict], model_name: str) -> str:
    response = await client.chat.completions.create(
        model=model_name, messages=messages, top_p=0.95, temperature=0.9
    )

    content: str = response.choices[0].message.content
    return content
