from fastapi import UploadFile
from pydantic import BaseModel
from typing import Literal

class DocumentProcess(BaseModel):
    files: list[UploadFile]
    type: Literal['pdf', 'images']
    name: str

class UpdateChunk(BaseModel):
    completed: bool