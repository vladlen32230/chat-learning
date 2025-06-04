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
    model: Literal['gemini-2.5-pro', 'gemini-2.5-flash']

class ChatResponse(BaseModel):
    text: str
    speech: UploadFile | None
