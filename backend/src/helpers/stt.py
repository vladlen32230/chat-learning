from openai import OpenAI
import os

def transcribe(
    audio_file: bytes,
) -> str:
    client = OpenAI(
        api_key=os.environ['DEEPINFRA_API_KEY'],
        base_url="https://api.deepinfra.com/v1/openai",
    )

    transcript = client.audio.transcriptions.create(
        model="openai/whisper-large-v3",
        file=audio_file
    )

    return transcript.text