from openai import OpenAI
from src.config_settings import DEEPINFRA_API_KEY


async def generate_speech(
    text: str, voice_name: str, file_format: str = "mp3"
) -> bytes:
    client = OpenAI(
        base_url="https://api.deepinfra.com/v1/openai", api_key=DEEPINFRA_API_KEY
    )

    binary_response: bytes = client.audio.speech.create(
        model="hexgrad/Kokoro-82M",
        voice=voice_name,
        input=text,
        response_format=file_format,
    ).content

    return binary_response
