"""Document analysis API endpoints using Claude AI."""
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, ProcessingStatus
from app.services.claude_analyzer import get_claude_analyzer

logger = logging.getLogger(__name__)
router = APIRouter()


class SummaryResponse(BaseModel):
    """Response for document summary."""
    document_id: UUID
    filename: str
    summary: str


class KeyTermsResponse(BaseModel):
    """Response for key terms extraction."""
    document_id: UUID
    filename: str
    analysis: dict


class QuestionRequest(BaseModel):
    """Request for asking a question."""
    question: str


class QuestionResponse(BaseModel):
    """Response for document question."""
    document_id: UUID
    filename: str
    question: str
    answer: str


class RiskAnalysisResponse(BaseModel):
    """Response for risk analysis."""
    document_id: UUID
    filename: str
    risk_analysis: str


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status."""
    available: bool
    model: str
    message: str


@router.get("/status", response_model=AnalysisStatusResponse)
def get_analysis_status():
    """Check if Claude AI analysis is available."""
    analyzer = get_claude_analyzer()
    from app.config import get_settings
    settings = get_settings()

    if analyzer.is_available():
        return AnalysisStatusResponse(
            available=True,
            model=settings.claude_model,
            message="Claude AI analysis is available"
        )
    return AnalysisStatusResponse(
        available=False,
        model=settings.claude_model,
        message="Claude API key not configured. Set ANTHROPIC_API_KEY in environment."
    )


@router.get("/{document_id}/summary", response_model=SummaryResponse)
async def get_document_summary(
    document_id: UUID,
    max_length: int = Query(500, ge=100, le=2000),
    db: Session = Depends(get_db),
):
    """
    Get an AI-generated summary of the document.

    Requires document to be fully processed.
    """
    analyzer = get_claude_analyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY."
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Status: {document.status.value}"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from document")

    summary = await analyzer.summarize(document.extracted_text, max_length)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")

    return SummaryResponse(
        document_id=document.id,
        filename=document.original_filename,
        summary=summary
    )


@router.get("/{document_id}/key-terms", response_model=KeyTermsResponse)
async def get_key_terms(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Extract key terms and entities from the document.

    Returns structured data including parties, dates, obligations, etc.
    """
    analyzer = get_claude_analyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY."
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Status: {document.status.value}"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from document")

    analysis = await analyzer.extract_key_terms(document.extracted_text)
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to extract key terms")

    return KeyTermsResponse(
        document_id=document.id,
        filename=document.original_filename,
        analysis=analysis
    )


@router.post("/{document_id}/ask", response_model=QuestionResponse)
async def ask_question(
    document_id: UUID,
    request: QuestionRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question about the document.

    The AI will answer based on the document content.
    """
    analyzer = get_claude_analyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY."
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Status: {document.status.value}"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from document")

    answer = await analyzer.answer_question(document.extracted_text, request.question)
    if not answer:
        raise HTTPException(status_code=500, detail="Failed to get answer")

    return QuestionResponse(
        document_id=document.id,
        filename=document.original_filename,
        question=request.question,
        answer=answer
    )


@router.get("/{document_id}/risks", response_model=RiskAnalysisResponse)
async def get_risk_analysis(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Analyze potential risks in the document.

    Returns identified risks with severity levels.
    """
    analyzer = get_claude_analyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY."
        )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not processed. Status: {document.status.value}"
        )

    if not document.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from document")

    risk_analysis = await analyzer.analyze_risks(document.extracted_text)
    if not risk_analysis:
        raise HTTPException(status_code=500, detail="Failed to analyze risks")

    return RiskAnalysisResponse(
        document_id=document.id,
        filename=document.original_filename,
        risk_analysis=risk_analysis
    )
