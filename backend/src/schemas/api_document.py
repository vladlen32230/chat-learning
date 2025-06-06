from pydantic import BaseModel
from src.models import Chunk, Document


class FullDocument(BaseModel):
    document: Document
    chunks: list[Chunk]
