from fastapi import APIRouter, HTTPException, Body
from src.models import Character
from src.database import get_session
from sqlmodel import select
from typing import Literal

router = APIRouter(prefix='/character', tags=['character'])


@router.post(
    '',
    response_model=Character,
    status_code=201,
    responses={}
)
async def create_character(
    name: str = Body(...),
    prompt_description: str = Body(...),
    voice_name: Literal['af_bella', 'af_nicole', 'af_heart', 'af_nova'] | None = Body(None)
):
    """
    Create a new character.

    1. It creates a new character in database with name, prompt description and optional voice name.
    2. It returns the character.
    """
    with get_session() as session:
        character = Character(
            name=name,
            prompt_description=prompt_description,
            voice_name=voice_name
        )
        session.add(character)
        session.flush()
        session.refresh(character)
        return character.model_dump()


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
        return [character.model_dump() for character in characters]


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
