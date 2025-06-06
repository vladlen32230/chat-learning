from fastapi import APIRouter, HTTPException, File, Form, UploadFile, Body
from src.schemas.api_document import FullDocument
from src.models import Document, Chunk
from src.database import get_session
from src.helpers.ocr import process_ocr
from src.helpers.chunking import chunk_text
import base64
import shutil
import asyncio
from pathlib import Path
from sqlmodel import select

router = APIRouter(prefix='/document', tags=['document'])

static_dir = Path("../static")

@router.get(
    '/{document_id}/full',
    response_model=FullDocument,
    status_code=200,
    responses={
        404: {'description': 'Document not found'}
    }
)
async def get_document(document_id: int):
    """
    Get a document with its chunks.

    1. It retrieves a document from database using its id.
    2. It retrieves all chunks from database using document id.
    3. It returns the document and its chunks.
    """
    with get_session() as session:
        document = session.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        chunks = session.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
        return FullDocument(document=document, chunks=chunks).model_dump()


@router.get(
    '',
    response_model=list[Document],
    status_code=200,
    responses={}
)
async def get_documents():
    """
    Get all documents.

    1. It retrieves all documents from database.
    2. It returns all documents.
    """
    with get_session() as session:
        documents = session.exec(select(Document)).all()
        return [document.model_dump() for document in documents]

@router.post(
    '',
    response_model=Document,
    status_code=201,
    responses={
        400: {'description': 'Invalid file type'}
    }
)
async def create_document(
    files: list[UploadFile] = File(...),
    name: str = Form(...)
):
    """
    Create a new document from PDF file or multiple images.

    1. It converts single PDF file or multiple images into text using OCR tools.
    2. It chunks text into logical parts.
    3. It creates a new document in database.
    4. It creates a new chunk in database for each logical part.
    5. It returns the document.
    """
    # Validate file types
    valid_files = []
    for file in files:
        content_type = file.content_type or ""
        filename = file.filename or ""
        
        if (content_type.startswith('application/pdf') or filename.lower().endswith('.pdf') or
            content_type.startswith('image/') or any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png'])):
            valid_files.append(file)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
    
    if not valid_files:
        raise HTTPException(status_code=400, detail="No valid PDF or image files found")
    
    # Prepare OCR requests for parallel processing
    ocr_tasks = []
    for file in valid_files:
        file_content = await file.read()
        
        # Determine file type for each individual file
        content_type = file.content_type or ""
        filename = file.filename or ""
        
        if content_type.startswith('application/pdf') or filename.lower().endswith('.pdf'):
            ocr_tasks.append(process_ocr(file_content, 'pdf'))
        else:  # images
            ocr_tasks.append(process_ocr(file_content, 'jpg'))
    
    # Process all OCR requests in parallel
    ocr_responses = await asyncio.gather(*ocr_tasks)
    
    # Process chunking for all OCR responses in parallel
    chunking_tasks = []
    for ocr_response in ocr_responses:
        chunking_tasks.append(chunk_text(ocr_response))
    
    chunks_lists = await asyncio.gather(*chunking_tasks)
    
    # Flatten all chunks into a single list
    all_chunks = []
    for chunks in chunks_lists:
        all_chunks.extend(chunks)
    
    # Create document in database
    with get_session() as session:
        # Create document with first file's name (or use a default name)
        document = Document(name=name)
        session.add(document)
        session.flush()  # Get the document ID
        
        # Create static directory for this document
        static_dir_path = static_dir / str(document.id)
        static_dir_path.mkdir(parents=True, exist_ok=True)
        
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
                file_path = static_dir_path / f"{chunk.id}.jpg"
                with open(file_path, 'wb') as f:
                    f.write(image_data)
            else:
                # Save as text file
                file_path = static_dir_path / f"{chunk.id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(chunk_content)
        
        session.refresh(document)
        return document.model_dump()


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
        
        static_dir_path = static_dir / str(document_id)
        
        # Delete all chunks associated with the document
        chunks = session.exec(select(Chunk).where(Chunk.document_id == document_id)).all()
        for chunk in chunks:
            session.delete(chunk)
        
        # Delete the document
        session.delete(document)
        
        # Delete files from static storage
        if static_dir_path.exists():
            shutil.rmtree(static_dir_path)


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
    completed: bool = Body(..., embed=True)
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
        chunk.completed = completed
        session.add(chunk)
        session.flush()
        session.refresh(chunk)
        
        return chunk.model_dump()