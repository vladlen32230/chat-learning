from fastapi import UploadFile
from pydantic import BaseModel
from typing import Literal
from src.models import Document, Chunk

class DocumentProcess(BaseModel):
    files: list[UploadFile]
    type: Literal['pdf', 'images']
    name: str

class UpdateChunk(BaseModel):
    completed: bool

class FullDocument(BaseModel):
    document: Document
    chunks: list[Chunk]