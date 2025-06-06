from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import document, character, chat
from src.database import engine
from src.models import Document, Chunk, Character
from sqlmodel import SQLModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
SQLModel.metadata.create_all(engine)

# Include routers
app.include_router(document.router)
app.include_router(character.router)
app.include_router(chat.router)
