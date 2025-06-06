from pydantic import BaseModel
from typing import Literal

class CreateCharacter(BaseModel):
    name: str
    prompt_description: str
    voice_name: Literal['af_bella', 'af_nicole', 'af_heart', 'af_nova'] | None = None
