from pydantic import BaseModel
from typing import Literal
from fastapi import UploadFile

class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str

class ChatRequest(BaseModel):
    character_id: int
    messages_history: list[Message]
    new_message_text: str | None
    new_message_speech: UploadFile | None
    model: Literal['google/gemini-2.5-pro-preview', 'google/gemini-2.5-flash-preview-05-20']

class ChatResponse(BaseModel):
    text: str
    speech: bytes | None
