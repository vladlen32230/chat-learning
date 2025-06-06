from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from src.database_con import engine
from src.db_models import Character, Chunk, Document
from src.routers import character_crud, chat_interaction, document_crud

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
app.include_router(document_crud.router)
app.include_router(character_crud.router)
app.include_router(chat_interaction.router)
