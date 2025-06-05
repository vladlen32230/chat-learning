from sqlmodel import SQLModel, Field
from typing import Literal

voiceNames = Literal['af_bella', 'af_nicole', 'af_heart', 'af_nova']

class Document(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str

class Chunk(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    type: Literal['image', 'text']
    document_id: int = Field(foreign_key="document.id")
    completed: bool = Field(default=False)

class Character(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    prompt_description: str
    voice_name: voiceNames | None
