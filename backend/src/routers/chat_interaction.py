import json
from typing import Any, Dict, List, Literal, Union

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from src.config_settings import STATIC_FILES_URL
from src.database_con import get_session
from src.db_models import Character, Chunk, Document
from src.helpers.chat_llm import chat_with_llm
from src.helpers.converting import convert_file_to_base64
from src.helpers.stt import transcribe
from src.helpers.tts import generate_speech
from src.schemas.api_chat import ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_character_and_validate_chunk(
    character_id: int, document_id: int, chunk_id: int
):
    """Helper function to retrieve character and validate document/chunk existence."""
    with get_session() as session:
        character = session.get(Character, character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Verify document exists
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Verify chunk exists and belongs to the document
        chunk = session.get(Chunk, chunk_id)
        if not chunk or chunk.document_id != document_id:
            raise HTTPException(status_code=404, detail="Chunk not found")

        session.expunge_all()
        return character, chunk


def _parse_messages_history(messages_history: str):
    """Helper function to parse and validate messages history."""
    try:
        parsed_messages_history = json.loads(messages_history)
        # Validate message structure
        for msg in parsed_messages_history:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise HTTPException(
                    status_code=400, detail="Invalid message format in messages_history"
                )
        return parsed_messages_history
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format for messages_history"
        )


async def _get_chunk_content(document_id: int, chunk: Chunk):
    """Helper function to retrieve chunk content from static file server."""
    chunk_content = None
    chunk_image_url = None

    if chunk.type == "text":
        file_path = f"{document_id}/{chunk.id}.txt"
        file_url = f"{STATIC_FILES_URL}/{file_path}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(file_url)
                response.raise_for_status()
                chunk_content = response.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Chunk file not found")

    else:  # image
        file_path = f"{document_id}/{chunk.id}.jpg"
        file_url = f"{STATIC_FILES_URL}/{file_path}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(file_url)
                response.raise_for_status()
                image_bytes = response.content
                chunk_image_url = convert_file_to_base64(image_bytes, "image/jpeg")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="Chunk file not found")

    return chunk_content, chunk_image_url


def _build_chat_messages(
    character: Character,
    chunk: Chunk,
    chunk_content: str,
    chunk_image_url: str,
    parsed_messages_history: list,
    user_message: str | None,
):
    """Helper function to build the chat messages for LLM."""
    messages: List[Dict[str, Union[str, List[Dict[str, Any]]]]] = [
        {
            "role": "system",
            "content": (
                f"This is your character's description: {character.prompt_description}\n\n"
                "Answer from the character's perspective only. Also return text without formatting."
                "Your response will be converted to character's voice."
            ),
        }
    ]

    # Add chunk content as context message
    if chunk.type == "text":
        messages.append(
            {
                "role": "system",
                "content": f"You are discussing the following text content: {chunk_content}",
            }
        )
    else:  # image
        messages.append(
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": "You are discussing the following image:"},
                    {"type": "image_url", "image_url": {"url": chunk_image_url}},
                ],
            }
        )

    # Add message history
    for msg in parsed_messages_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add new user message
    if user_message:
        messages.append({"role": "user", "content": user_message})

    return messages


@router.post(
    "/document/{document_id}/chunk/{chunk_id}",
    response_model=ChatResponse,
    status_code=200,
    responses={404: {"description": "Character not found or chunk not found"}},
)
async def chat(
    document_id: int,
    chunk_id: int,
    character_id: int = Form(...),
    messages_history: str = Form(...),  # JSON string
    new_message_text: str | None = Form(None),
    new_message_speech: UploadFile | None = File(None),
    model: Literal[
        "google/gemini-2.5-pro-preview", "google/gemini-2.5-flash-preview-05-20"
    ] = Form(...),
):
    """
    Chat with the character about chunk.

    1. It retrieves character from database using its id.
    2. It retrieves chunk data (text or image) from local storage using database id.
    3. It generates a prompt for LLM using character's prompt description, chunk data and history of messages.
    4. If character id is specified, also generates speech of the text.
    5. Returns response with text and speech if character has voice name.
    """
    # Step 1: Retrieve character and validate chunk
    character, chunk = _get_character_and_validate_chunk(
        character_id, document_id, chunk_id
    )

    # Parse messages_history from JSON string
    parsed_messages_history = _parse_messages_history(messages_history)

    # Step 2: Retrieve chunk data from static file server
    chunk_content, chunk_image_url = await _get_chunk_content(document_id, chunk)

    # Handle speech-to-text if audio is provided
    user_message = new_message_text
    if new_message_speech:
        audio_content = await new_message_speech.read()
        user_message = transcribe(audio_content)

    # Step 3: Generate prompt for LLM using character's prompt, chunk data, and history
    messages = _build_chat_messages(
        character,
        chunk,
        chunk_content,
        chunk_image_url,
        parsed_messages_history,
        user_message,
    )

    # Get response from LLM
    response_text = await chat_with_llm(messages, model)

    # Step 4: Generate speech if character has voice name
    speech_content = None
    if character.voice_name:
        speech_bytes = await generate_speech(response_text, character.voice_name)
        speech_content = convert_file_to_base64(speech_bytes, "audio/mp3")

    # Step 5: Return response
    return ChatResponse(
        text=response_text, speech=speech_content, input_user_text=user_message
    ).model_dump()
