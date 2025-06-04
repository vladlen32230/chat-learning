from fastapi import UploadFile
from pydantic import BaseModel

class PDF(BaseModel):
    file: UploadFile

class Images(BaseModel):
    files: list[UploadFile]

class UpdateChunk(BaseModel):
    completed: bool