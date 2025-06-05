from fastapi import APIRouter, HTTPException
from src.schemas.api_character import CreateCharacter, UpdateCharacter
from src.models import Character
from src.database import get_session
from sqlmodel import select

router = APIRouter(prefix='/character', tags=['character'])


@router.post(
    '',
    response_model=Character,
    status_code=201,
    responses={}
)
async def create_character(
    request: CreateCharacter
):
    """
    Create a new character.

    1. It creates a new character in database with name, prompt description and optional voice name.
    2. It returns the character.
    """
    with get_session() as session:
        character = Character(
            name=request.name,
            prompt_description=request.prompt_description,
            voice_name=request.voice_name
        )
        session.add(character)
        session.flush()
        session.refresh(character)
        return character


@router.get(
    '',
    response_model=list[Character],
    status_code=200,
    responses={}
)
async def get_characters():
    """
    Get all characters.

    1. It retrieves all characters from database.
    2. It returns a list of characters.
    """
    with get_session() as session:
        characters = session.exec(select(Character)).all()
        return characters


@router.delete(
    '/{character_id}',
    status_code=204,
    responses={
        404: {"description": "Character not found"}
    }
)
async def delete_character(
    character_id: int
):
    """
    Delete a character.

    1. It deletes a character from database.
    """
    with get_session() as session:
        # Check if character exists
        character = session.get(Character, character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # Delete the character
        session.delete(character)
