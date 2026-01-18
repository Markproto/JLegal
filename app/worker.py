"""Celery worker for background document processing."""
import json
import logging
from datetime import datetime

from celery import Celery
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.services.document_processor import DocumentProcessor

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "jlegal",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    worker_prefetch_multiplier=1,  # Fair scheduling
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-documents": {
        "task": "app.worker.cleanup_old_documents",
        "schedule": 86400.0,  # Daily
    },
}


def get_db() -> Session:
    """Get database session for worker tasks."""
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str) -> dict:
    """
    Process a document in the background.

    Args:
        document_id: UUID of the document to process

    Returns:
        Dict with processing results
    """
    db = get_db()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"error": "Document not found"}

        # Update status to processing
        document.status = ProcessingStatus.PROCESSING
        document.task_id = self.request.id
        db.commit()

        logger.info(f"Processing document: {document.original_filename}")

        # Process the document
        processor = DocumentProcessor()
        result = processor.process(document.file_path, document.mime_type)

        # Update document with results
        document.extracted_text = result["extracted_text"]
        document.page_count = result.get("page_count")
        document.word_count = result.get("word_count")
        document.metadata_json = json.dumps(result.get("metadata", {}))
        document.status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()
        document.error_message = None
        db.commit()

        logger.info(f"Document {document_id} processed successfully")

        return {
            "document_id": str(document_id),
            "status": "completed",
            "word_count": document.word_count,
            "page_count": document.page_count,
        }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")

        # Update document with error
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = ProcessingStatus.FAILED
                document.error_message = str(e)
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update document status: {db_err}")

        # Retry if attempts remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"error": str(e)}

    finally:
        db.close()


@celery_app.task
def cleanup_old_documents(days: int = 30) -> dict:
    """
    Clean up documents older than specified days.

    This is a scheduled task that runs daily.
    """
    from datetime import timedelta
    from app.utils.file_utils import delete_file

    db = get_db()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        old_documents = db.query(Document).filter(Document.created_at < cutoff).all()

        deleted_count = 0
        for doc in old_documents:
            try:
                delete_file(doc.filename)
                db.delete(doc)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting document {doc.id}: {e}")

        db.commit()
        logger.info(f"Cleaned up {deleted_count} old documents")

        return {"deleted": deleted_count}

    finally:
        db.close()


@celery_app.task
def reprocess_failed_documents() -> dict:
    """Reprocess all failed documents."""
    db = get_db()
    try:
        failed_docs = db.query(Document).filter(
            Document.status == ProcessingStatus.FAILED
        ).all()

        requeued = 0
        for doc in failed_docs:
            doc.status = ProcessingStatus.PENDING
            doc.error_message = None
            db.commit()
            process_document.delay(str(doc.id))
            requeued += 1

        logger.info(f"Requeued {requeued} failed documents")
        return {"requeued": requeued}

    finally:
        db.close()
