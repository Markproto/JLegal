# JLegal Deployment Guide

## Digital Ocean Droplet Deployment

### Target Server
- **IP:** 64.23.156.217
- **Specs:** 2 vCPU, 4GB RAM, 80GB Disk
- **OS:** Ubuntu (recommended 22.04 or 24.04)

### Step 1: Connect to Server

```bash
ssh root@64.23.156.217
```

### Step 2: Run Server Setup

```bash
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/<your-repo>/main/scripts/setup-server.sh | bash
```

Or manually:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure firewall
ufw allow OpenSSH
ufw allow 8000/tcp
ufw allow 5555/tcp
ufw --force enable
```

### Step 3: Clone Repository

```bash
mkdir -p /opt/jlegal
cd /opt/jlegal
git clone <your-repo-url> .
```

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
```

Key settings to review:
- `SECRET_KEY` - Change to a random string
- `MAX_UPLOAD_SIZE` - Default 100MB
- `WORKERS_PER_CONTAINER` - Default 4 (good for 4GB RAM)

### Step 5: Deploy

```bash
./scripts/deploy.sh
```

### Step 6: Verify

```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f

# Test API
curl http://64.23.156.217:8000/health
```

## API Usage

### Upload a Document

```bash
curl -X POST -F "file=@document.pdf" http://64.23.156.217:8000/api/v1/documents/upload
```

Response:
```json
{
  "id": "abc123...",
  "status": "pending",
  "original_filename": "document.pdf"
}
```

### Check Status

```bash
curl http://64.23.156.217:8000/api/v1/documents/{id}/status
```

### Get Extracted Text

```bash
curl http://64.23.156.217:8000/api/v1/documents/{id}/text
```

## Scaling for Higher Capacity

### Scale Workers

```bash
# Scale to 8 workers (for heavy loads)
docker-compose up -d --scale worker=8

# Check worker count
docker-compose ps | grep worker
```

### Memory Considerations

- Each worker uses ~500MB RAM for OCR
- 4GB droplet: 4-6 workers recommended
- 8GB droplet: 8-12 workers recommended

## Monitoring

### Flower (Task Monitor)

Access at: http://64.23.156.217:5555

Shows:
- Active tasks
- Task history
- Worker status
- Queue lengths

### API Stats

```bash
curl http://64.23.156.217:8000/stats
```

Returns document processing statistics.

## Backup & Restore

### Create Backup

```bash
./scripts/backup.sh
```

Backups stored in `/opt/jlegal-backups/`

### Restore from Backup

```bash
./scripts/restore.sh /opt/jlegal-backups/jlegal_backup_20240101_120000.tar.gz
```

## Troubleshooting

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Restart Services

```bash
docker-compose restart
```

### Database Issues

```bash
# Connect to database
docker-compose exec db psql -U jlegal -d jlegal

# Run migrations manually
docker-compose exec api alembic upgrade head
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Remove old documents (via API or database)
```

## Security Recommendations

1. **Change default passwords** in `.env`
2. **Set up SSL** with Let's Encrypt
3. **Restrict Flower access** (remove from docker-compose or add authentication)
4. **Configure firewall** to only allow necessary ports
5. **Enable automatic security updates**

## SSL Setup (Optional)

```bash
# Install certbot
apt install certbot

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Configure nginx as reverse proxy with SSL
```
