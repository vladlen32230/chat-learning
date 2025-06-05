from pydantic import BaseModel
from src.models import voiceNames

class CreateCharacter(BaseModel):
    name: str
    prompt_description: str
    voice_name: voiceNames | None = None
