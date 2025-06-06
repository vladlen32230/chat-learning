from openai import OpenAI
from src.config_settings import DEEPINFRA_API_KEY

client = OpenAI(
    api_key=DEEPINFRA_API_KEY,
    base_url="https://api.deepinfra.com/v1/openai",
)


def transcribe(
    audio_file: bytes,
) -> str:
    transcript: str = client.audio.transcriptions.create(
        model="openai/whisper-large-v3", file=audio_file
    ).text

    return transcript
