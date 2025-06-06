from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from src.schemas.api_chat import ChatResponse, Message
from src.models import Character, Chunk, Document
from src.database import get_session
from src.helpers.chat import chat_with_llm
from src.helpers.stt import transcribe
from src.helpers.tts import generate_speech
from src.helpers.other import convert_file_to_base64
from pathlib import Path
from typing import Literal
import json

router = APIRouter(prefix='/chat', tags=['chat'])

static_dir = Path("../static")


@router.post(
    '/document/{document_id}/chunk/{chunk_id}',
    response_model=ChatResponse,
    status_code=200,
    responses={
        404: {
            'description': 'Character not found or chunk not found'
        }
    }
)
async def chat(
    document_id: int, 
    chunk_id: int, 
    character_id: int = Form(...),
    messages_history: str = Form(...),  # JSON string
    new_message_text: str | None = Form(None),
    new_message_speech: UploadFile | None = File(None),
    model: Literal['google/gemini-2.5-pro-preview', 'google/gemini-2.5-flash-preview-05-20'] = Form(...),
):
    """
    Chat with the character about chunk.

    1. It retrieves character from database using its id.
    2. It retrieves chunk data (text or image) from local storage using database id.
    3. It generates a prompt for LLM using character's prompt description, chunk data and history of messages.
    4. If character id is specified, also generates speech of the text.
    5. Returns response with text and speech if character has voice name.
    """
    # Step 1: Retrieve character from database
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
    
    # Parse messages_history from JSON string
    try:
        parsed_messages_history = json.loads(messages_history)
        # Validate message structure
        for msg in parsed_messages_history:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise HTTPException(status_code=400, detail="Invalid message format in messages_history")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for messages_history")
    
    # Step 2: Retrieve chunk data from local storage
    static_dir_document = static_dir / str(document_id)
    chunk_content = None
    chunk_image_url = None
    
    if chunk.type == "text":
        chunk_file_path = static_dir_document / f"{chunk_id}.txt"
        if not chunk_file_path.exists():
            raise HTTPException(status_code=404, detail="Chunk file not found")
        with open(chunk_file_path, 'r', encoding='utf-8') as f:
            chunk_content = f.read()
    else:  # image
        chunk_file_path = static_dir_document / f"{chunk_id}.jpg"
        if not chunk_file_path.exists():
            raise HTTPException(status_code=404, detail="Chunk file not found")
        # Read image and convert to base64 for LLM
        with open(chunk_file_path, 'rb') as f:
            image_bytes = f.read()
        chunk_image_url = convert_file_to_base64(image_bytes, 'image/jpeg')
    
    # Handle speech-to-text if audio is provided
    user_message = new_message_text
    if new_message_speech:
        audio_content = await new_message_speech.read()
        user_message = transcribe(audio_content)
    
    # Step 3: Generate prompt for LLM using character's prompt, chunk data, and history
    messages = [
        {
            "role": "system",
            "content": (
                f"This is your character's description: {character.prompt_description}\n\n"
                "Answer from the character's perspective only. Also return text without formatting."
                "Your response will be converted to character's voice."
            )
        }
    ]
    
    # Add chunk content as context message
    if chunk.type == "text":
        messages.append({
            "role": "system",
            "content": f"You are discussing the following text content: {chunk_content}"
        })
    else:  # image
        messages.append({
            "role": "system", 
            "content": [
                {
                    "type": "text",
                    "text": "You are discussing the following image:"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": chunk_image_url
                    }
                }
            ]
        })
    
    # Add message history
    for msg in parsed_messages_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add new user message
    if user_message:
        messages.append({
            "role": "user",
            "content": user_message
        })
    
    # Get response from LLM
    response_text = await chat_with_llm(messages, model)
    
    # Step 4: Generate speech if character has voice name
    speech_content = None
    if character.voice_name:
        speech_bytes = await generate_speech(response_text, character.voice_name)
        speech_content = convert_file_to_base64(speech_bytes, 'audio/mp3')
    
    # Step 5: Return response
    return ChatResponse(
        text=response_text,
        speech=speech_content,
        input_user_text=user_message
    ).model_dump()