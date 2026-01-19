"""Document analysis API endpoints using Claude AI."""
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document, ProcessingStatus, DocumentCategory
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


class SearchAllRequest(BaseModel):
    """Request for searching all documents."""
    query: str
    include_case_law: bool = True


class SearchResult(BaseModel):
    """Single search result."""
    document_id: UUID
    filename: str
    category: str
    answer: str
    relevance: str  # "high", "medium", "low"


class SearchAllResponse(BaseModel):
    """Response for searching all documents."""
    query: str
    total_searched: int
    results: list[SearchResult]
    case_law_referenced: int


@router.post("/search-all", response_model=SearchAllResponse)
async def search_all_documents(
    request: SearchAllRequest,
    db: Session = Depends(get_db),
):
    """
    Search across all documents with optional case law cross-referencing.

    This endpoint:
    1. Gathers all case law documents from the reference library
    2. Searches each regular document for the query
    3. Cross-references with case law to identify violations or matches
    """
    analyzer = get_claude_analyzer()
    if not analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="Claude API not configured. Set ANTHROPIC_API_KEY."
        )

    # Get case law documents for reference
    case_law_docs = []
    if request.include_case_law:
        case_law_query = db.query(Document).filter(
            Document.category.in_([DocumentCategory.CASE_LAW, DocumentCategory.REGULATION]),
            Document.status == ProcessingStatus.COMPLETED
        ).all()

        for doc in case_law_query:
            if doc.extracted_text:
                # Limit each case law to first 2000 chars for context
                case_law_docs.append({
                    "name": doc.original_filename,
                    "excerpt": doc.extracted_text[:2000]
                })

    # Build case law context for the prompt
    case_law_context = ""
    if case_law_docs:
        case_law_context = "\n\n=== LEGAL REFERENCES (Case Law & Regulations) ===\n"
        for cl in case_law_docs[:10]:  # Limit to 10 references
            case_law_context += f"\n--- {cl['name']} ---\n{cl['excerpt']}\n"

    # Get regular documents to search
    regular_docs = db.query(Document).filter(
        Document.category == DocumentCategory.REGULAR,
        Document.status == ProcessingStatus.COMPLETED
    ).all()

    results = []
    for doc in regular_docs:
        if not doc.extracted_text:
            continue

        # Build the search prompt with case law context
        prompt = f"""Analyze this document for the following query: "{request.query}"

{case_law_context}

=== DOCUMENT TO ANALYZE: {doc.original_filename} ===
{doc.extracted_text[:8000]}

Instructions:
1. Search for content matching the query
2. If case law or regulations are provided above, cross-reference to identify potential violations or matches
3. Quote relevant text from the document
4. Indicate where in the document the match appears (beginning, middle, end)
5. If referencing case law, cite the specific case/regulation name
6. Rate the relevance as HIGH, MEDIUM, or LOW

If nothing relevant is found, respond with exactly: "NO_MATCH"
"""
        try:
            answer = await analyzer.answer_question(doc.extracted_text, prompt)

            if answer and "NO_MATCH" not in answer.upper():
                # Determine relevance from the answer
                relevance = "medium"
                if "HIGH" in answer.upper():
                    relevance = "high"
                elif "LOW" in answer.upper():
                    relevance = "low"

                results.append(SearchResult(
                    document_id=doc.id,
                    filename=doc.original_filename,
                    category=doc.category.value,
                    answer=answer,
                    relevance=relevance
                ))
        except Exception as e:
            logger.error(f"Error searching document {doc.id}: {e}")
            continue

    # Sort by relevance
    relevance_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: relevance_order.get(x.relevance, 1))

    return SearchAllResponse(
        query=request.query,
        total_searched=len(regular_docs),
        results=results,
        case_law_referenced=len(case_law_docs)
    )
