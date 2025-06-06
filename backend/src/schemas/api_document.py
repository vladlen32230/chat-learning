from pydantic import BaseModel
from src.models import Document, Chunk

class FullDocument(BaseModel):
    document: Document
    chunks: list[Chunk]