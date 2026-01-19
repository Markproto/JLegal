"""Pydantic schemas for document API."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.document import ProcessingStatus, DocumentCategory


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str
    mime_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    category: DocumentCategory = DocumentCategory.REGULAR
    status: ProcessingStatus
    error_message: Optional[str] = None
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    document_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""
    total: int
    documents: List[DocumentResponse]


class ProcessingStatusResponse(BaseModel):
    """Schema for processing status response."""
    id: UUID
    status: ProcessingStatus
    error_message: Optional[str] = None
    progress: Optional[str] = None


class DocumentTextResponse(BaseModel):
    """Schema for extracted text response."""
    id: UUID
    original_filename: str
    extracted_text: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
