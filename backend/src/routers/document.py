from fastapi import APIRouter
from src.schemas.api_document import DocumentProcess, UpdateChunk
from src.models import Document, Chunk

router = APIRouter(prefix='/document', tags=['document'])


@router.post(
    '',
    response_model=Document,
    status_code=201,
    responses={}
)
async def create_document(
    request: DocumentProcess
):
    """
    Create a new document from PDF file or multiple images.

    1. It converts single PDF file or multiple images into text using OCR tools.
    2. It chunks text into logical parts.
    3. It creates a new document in database.
    4. It creates a new chunk in database for each logical part.
    5. It returns the document.
    """
    pass


@router.delete(
    '/{document_id}',
    status_code=204,
    responses={}
)
async def delete_document(
    document_id: int
):
    """
    Delete a document.

    1. It deletes a document from database.
    2. It deletes all chunks from database.
    3. It deletes all files from local storage.
    """
    pass


@router.put(
    '/{document_id}/chunk/{chunk_id}',
    status_code=200,
    response_model=Chunk,
    responses={
        404: {
            'description': 'Document or chunk not found'
        }
    }
)
async def update_chunk(
    document_id: int,
    request: UpdateChunk
):
    """
    Update a chunk.

    1. It updates a chunk in database, setting completed field to True or False.
    2. It returns the chunk.
    """
    pass