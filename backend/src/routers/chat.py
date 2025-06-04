from fastapi import APIRouter
from src.schemas.api_chat import ChatRequest, ChatResponse

router = APIRouter(prefix='/chat', tags=['chat'])


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
    request: ChatRequest
):
    """
    Chat with the character about chunk.

    1. It retrieves character from database using its id.
    2. It retrieves chunk data (text or image) from local storage using database id.
    3. It generates a prompt for LLM using character's prompt description, chunk data and history of messages.
    4. If character id is specified, also generates speech of the text.
    5. Returns response with text and speech if character has voice name.
    """
    pass