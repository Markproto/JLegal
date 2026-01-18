#!/bin/bash
# JLegal Backup Script
# Creates backups of documents and database

set -e

BACKUP_DIR="/opt/jlegal-backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="jlegal_backup_$DATE"

echo "Creating backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup database
echo "Backing up database..."
docker-compose exec -T db pg_dump -U jlegal jlegal > "$BACKUP_DIR/$BACKUP_NAME/database.sql"

# Backup storage (documents)
echo "Backing up documents..."
docker cp $(docker-compose ps -q api):/app/storage "$BACKUP_DIR/$BACKUP_NAME/storage"

# Create archive
echo "Creating archive..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo "Backup complete: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Optional: Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
echo "Cleaned up old backups"
