"""Document API endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, ProcessingStatus, DocumentCategory
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    ProcessingStatusResponse,
    DocumentTextResponse,
)
from app.services.document_processor import DocumentProcessor
from app.utils.file_utils import save_upload_file, delete_file
from app.worker import process_document
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Query(DocumentCategory.REGULAR, description="Document category"),
    db: Session = Depends(get_db),
):
    """
    Upload a document for processing.

    Supported formats: PDF, DOCX, DOC, RTF, TXT, PNG, JPG, TIFF

    Categories:
    - regular: Documents to analyze
    - case_law: Case law references for cross-referencing
    - regulation: Regulations and statutes
    - template: Contract templates
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size // 1024 // 1024}MB",
        )

    # Detect and validate MIME type
    processor = DocumentProcessor()

    # Save file temporarily to detect MIME type
    try:
        unique_filename, file_path, actual_size = await save_upload_file(file)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")

    # Detect MIME type
    mime_type = processor.detect_mime_type(file_path)

    if not processor.is_supported(mime_type):
        delete_file(unique_filename)
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}. Supported: PDF, DOCX, DOC, RTF, TXT, images",
        )

    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        mime_type=mime_type,
        file_size=actual_size,
        file_path=file_path,
        category=category,
        status=ProcessingStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue for processing
    task = process_document.delay(str(document.id))
    document.task_id = task.id
    db.commit()

    logger.info(f"Document {document.id} queued for processing")

    return document


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ProcessingStatus] = None,
    category: Optional[DocumentCategory] = None,
    db: Session = Depends(get_db),
):
    """List all documents with optional filtering."""
    query = db.query(Document)

    if status:
        query = query.filter(Document.status == status)

    if category:
        query = query.filter(Document.category == category)

    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    return DocumentListResponse(total=total, documents=documents)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Get document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
def get_processing_status(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Get document processing status."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    progress = None
    if document.status == ProcessingStatus.PROCESSING:
        progress = "Processing document..."
    elif document.status == ProcessingStatus.COMPLETED:
        progress = "Complete"

    return ProcessingStatusResponse(
        id=document.id,
        status=document.status,
        error_message=document.error_message,
        progress=progress,
    )


@router.get("/{document_id}/text", response_model=DocumentTextResponse)
def get_document_text(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Get extracted text from document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not yet processed. Status: {document.status.value}",
        )

    return DocumentTextResponse(
        id=document.id,
        original_filename=document.original_filename,
        extracted_text=document.extracted_text,
        word_count=document.word_count,
        page_count=document.page_count,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    try:
        delete_file(document.filename)
    except Exception as e:
        logger.warning(f"Error deleting file: {e}")

    # Delete record
    db.delete(document)
    db.commit()

    return {"message": "Document deleted", "id": str(document_id)}


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """Reprocess a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Reset status
    document.status = ProcessingStatus.PENDING
    document.error_message = None
    document.extracted_text = None
    db.commit()

    # Queue for reprocessing
    task = process_document.delay(str(document.id))
    document.task_id = task.id
    db.commit()

    return document
