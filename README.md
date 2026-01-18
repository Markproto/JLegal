# JLegal - Legal Document Processor

A scalable legal document processing system designed for deployment on Digital Ocean with unlimited processing capacity.

## Features

- **Document Processing**: Extract text from PDF, DOCX, images (OCR), and plain text files
- **Unlimited Capacity**: Queue-based architecture with Celery workers that scale horizontally
- **REST API**: Simple HTTP API for document upload, processing, and retrieval
- **OCR Support**: Tesseract-based OCR for scanned documents and images
- **Metadata Extraction**: Automatic extraction of document metadata
- **Search Ready**: Processed text ready for full-text search integration

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FastAPI       │────▶│   Redis         │────▶│   Celery        │
│   (API Server)  │     │   (Task Queue)  │     │   (Workers)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │               ┌─────────────────┐             │
        └──────────────▶│   PostgreSQL    │◀────────────┘
                        │   (Metadata)    │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   File Storage  │
                        │   (Documents)   │
                        └─────────────────┘
```

## Quick Start (Digital Ocean Deployment)

### Prerequisites

- Docker and Docker Compose installed on your droplet
- At least 2GB RAM (4GB+ recommended for OCR)
- Sufficient disk space for document storage

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd JLegal
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. The API will be available at `http://your-droplet-ip:8000`

## API Endpoints

### Upload Document
```bash
POST /api/v1/documents/upload
Content-Type: multipart/form-data

curl -X POST -F "file=@document.pdf" http://localhost:8000/api/v1/documents/upload
```

### Check Processing Status
```bash
GET /api/v1/documents/{document_id}/status

curl http://localhost:8000/api/v1/documents/{document_id}/status
```

### Get Processed Document
```bash
GET /api/v1/documents/{document_id}

curl http://localhost:8000/api/v1/documents/{document_id}
```

### List All Documents
```bash
GET /api/v1/documents

curl http://localhost:8000/api/v1/documents
```

### Health Check
```bash
GET /health

curl http://localhost:8000/health
```

## Scaling Workers

To increase processing capacity, scale the Celery workers:

```bash
docker-compose up -d --scale worker=4
```

## Supported File Types

- PDF (`.pdf`) - Native text extraction + OCR for scanned pages
- Microsoft Word (`.docx`, `.doc`)
- Images (`.png`, `.jpg`, `.jpeg`, `.tiff`) - OCR extraction
- Plain Text (`.txt`)
- Rich Text Format (`.rtf`)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://jlegal:jlegal@db:5432/jlegal` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `STORAGE_PATH` | Document storage path | `/app/storage` |
| `MAX_UPLOAD_SIZE` | Maximum upload size in bytes | `104857600` (100MB) |
| `WORKERS_PER_CONTAINER` | Celery workers per container | `4` |
| `OCR_LANGUAGES` | Tesseract OCR languages | `eng` |

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start services (requires Redis and PostgreSQL)
uvicorn app.main:app --reload
celery -A app.worker worker --loglevel=info
```

## License

MIT License
