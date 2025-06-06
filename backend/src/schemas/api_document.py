from pydantic import BaseModel
from src.db_models import Chunk, Document


class FullDocument(BaseModel):
    document: Document
    chunks: list[Chunk]
