# CLAUDE.md - Project Context for Claude Code

## Project Overview

JLegal is a legal document processing system with unlimited capacity, designed for deployment on Digital Ocean droplets. It extracts text from PDFs, Word documents, and images (OCR) and stores the results in a searchable database.

## Tech Stack

- **Backend:** Python 3.11, FastAPI
- **Task Queue:** Celery with Redis
- **Database:** PostgreSQL
- **OCR:** Tesseract
- **AI Analysis:** Claude API (Anthropic)
- **Containerization:** Docker, Docker Compose

## Project Structure

```
JLegal/
├── app/
│   ├── api/v1/             # REST API endpoints
│   │   └── documents.py    # Document upload/management
│   ├── models/             # SQLAlchemy models
│   │   └── document.py     # Document model
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   │   └── document_processor.py  # Text extraction
│   ├── utils/              # Utilities
│   ├── config.py           # Configuration
│   ├── database.py         # Database setup
│   ├── main.py             # FastAPI app
│   └── worker.py           # Celery worker
├── alembic/                # Database migrations
├── scripts/                # Deployment scripts
│   ├── deploy.sh           # Main deployment
│   ├── setup-server.sh     # Server setup
│   ├── backup.sh           # Backup script
│   └── restore.sh          # Restore script
├── docker-compose.yml      # Docker services
├── Dockerfile              # Application image
├── requirements.txt        # Python dependencies
└── .env.example            # Environment template
```

## Key Commands

```bash
# Development
pip install -r requirements.txt
uvicorn app.main:app --reload
celery -A app.worker worker --loglevel=info

# Production (Docker)
docker-compose up -d                    # Start all services
docker-compose logs -f                  # View logs
docker-compose up -d --scale worker=4   # Scale workers
docker-compose down                     # Stop services

# Database
alembic upgrade head                    # Run migrations
alembic revision --autogenerate -m "msg" # Create migration
```

## API Endpoints

### Document Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/documents/upload` | POST | Upload document |
| `/api/v1/documents` | GET | List documents |
| `/api/v1/documents/{id}` | GET | Get document |
| `/api/v1/documents/{id}/status` | GET | Check processing status |
| `/api/v1/documents/{id}/text` | GET | Get extracted text |
| `/api/v1/documents/{id}` | DELETE | Delete document |

### AI Analysis (Claude)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/analysis/status` | GET | Check if Claude AI is available |
| `/api/v1/analysis/{id}/summary` | GET | Get AI summary of document |
| `/api/v1/analysis/{id}/key-terms` | GET | Extract key terms & entities |
| `/api/v1/analysis/{id}/ask` | POST | Ask questions about document |
| `/api/v1/analysis/{id}/risks` | GET | Analyze potential risks |

### System
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/stats` | GET | Processing statistics |

## Environment Variables

```
DATABASE_URL=postgresql://jlegal:jlegal@db:5432/jlegal
REDIS_URL=redis://redis:6379/0
STORAGE_PATH=/app/storage
MAX_UPLOAD_SIZE=104857600
WORKERS_PER_CONTAINER=4
OCR_LANGUAGES=eng
SECRET_KEY=change-in-production
ANTHROPIC_API_KEY=your-api-key-here
CLAUDE_MODEL=claude-sonnet-4-20250514
```

## Deployment Target

- **Server:** Digital Ocean Droplet
- **IP:** 64.23.156.217
- **Specs:** 2 vCPU, 4GB RAM, 80GB Disk
- **Region:** SFO3

## Deployment Steps

1. SSH to server: `ssh root@64.23.156.217`
2. Run setup: `./scripts/setup-server.sh`
3. Clone repo to `/opt/jlegal`
4. Configure `.env`
5. Run `./scripts/deploy.sh`

## Supported File Types

- PDF (.pdf) - Native + OCR
- Word (.docx, .doc)
- RTF (.rtf)
- Plain text (.txt)
- Images (.png, .jpg, .jpeg, .tiff) - OCR

## Architecture Notes

- **Unlimited Capacity:** Celery workers can be scaled horizontally
- **Queue-based:** All document processing is asynchronous
- **Fault-tolerant:** Failed tasks retry automatically
- **Stateless API:** Easy to load balance
