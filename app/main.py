"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.database import engine
from app.models import Document

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting JLegal Document Processor")
    yield
    logger.info("Shutting down JLegal Document Processor")


app = FastAPI(
    title="JLegal Document Processor",
    description="Legal document processing API with OCR support and unlimited capacity",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "JLegal Document Processor",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    from sqlalchemy import text

    try:
        # Check database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check Redis connection
    try:
        from redis import Redis
        redis = Redis.from_url(settings.redis_url)
        redis.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
    }


@app.get("/stats")
def get_stats():
    """Get processing statistics."""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.document import ProcessingStatus

    db = SessionLocal()
    try:
        total = db.query(Document).count()
        pending = db.query(Document).filter(Document.status == ProcessingStatus.PENDING).count()
        processing = db.query(Document).filter(Document.status == ProcessingStatus.PROCESSING).count()
        completed = db.query(Document).filter(Document.status == ProcessingStatus.COMPLETED).count()
        failed = db.query(Document).filter(Document.status == ProcessingStatus.FAILED).count()

        return {
            "total_documents": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
        }
    finally:
        db.close()
