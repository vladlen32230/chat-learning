from fastapi import APIRouter, HTTPException
from src.schemas.api_document import DocumentProcess, UpdateChunk
from src.models import Document, Chunk
from src.database import get_session
from src.helpers.ocr import process_ocr
from src.helpers.chunking import chunk_text
import base64
import shutil
from pathlib import Path
from sqlmodel import select

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
    # Process files through OCR
    all_chunks = []
    
    for file in request.files:
        file_content = await file.read()
        
        if request.type == 'pdf':
            ocr_response = await process_ocr(file_content, 'pdf')
        else:  # images
            ocr_response = await process_ocr(file_content, 'jpg')
        
        # Chunk the OCR response
        chunks = await chunk_text(ocr_response)
        all_chunks.extend(chunks)
    
    # Create document in database
    with get_session() as session:
        # Create document with first file's name (or use a default name)
        document = Document(name=request.name)
        session.add(document)
        session.flush()  # Get the document ID
        
        # Create static directory for this document
        static_dir = Path("static") / str(document.id)
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each chunk and create database entries
        for chunk_content in all_chunks:
            # Determine chunk type based on content
            is_base64_image = chunk_content.startswith('data:image/jpeg;base64,')
            chunk_type = 'image' if is_base64_image else 'text'
            
            # Create chunk in database
            chunk = Chunk(
                type=chunk_type,
                document_id=document.id,
                completed=False
            )
            session.add(chunk)
            session.flush()  # Get the chunk ID
            
            # Save chunk content to static file
            if chunk_type == 'image':
                # Extract base64 data and save as JPG
                base64_data = chunk_content.split(',')[1]
                image_data = base64.b64decode(base64_data)
                file_path = static_dir / f"{chunk.id}.jpg"
                with open(file_path, 'wb') as f:
                    f.write(image_data)
            else:
                # Save as text file
                file_path = static_dir / f"{chunk.id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)
        
        session.refresh(document)
        return document


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
    with get_session() as session:
        # Check if document exists
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete all chunks associated with the document
        chunks = session.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
        for chunk in chunks:
            session.delete(chunk)
        
        # Delete the document
        session.delete(document)
        
        # Delete files from static storage
        static_dir = Path("static") / str(document_id)
        if static_dir.exists():
            shutil.rmtree(static_dir)


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
    chunk_id: int,
    request: UpdateChunk
):
    """
    Update a chunk.

    1. It updates a chunk in database, setting completed field to True or False.
    2. It returns the chunk.
    """
    with get_session() as session:
        # Check if document exists
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get the chunk
        chunk = session.get(Chunk, chunk_id)
        if not chunk or chunk.document_id != document_id:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # Update the chunk
        chunk.completed = request.completed
        session.add(chunk)
        session.refresh(chunk)
        
        return chunk