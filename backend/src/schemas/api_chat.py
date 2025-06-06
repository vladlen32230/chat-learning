from pydantic import BaseModel
from typing import Literal

class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str

class ChatResponse(BaseModel):
    text: str
    speech: str | None #base 64
    input_user_text: str | None
