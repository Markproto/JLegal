#!/bin/bash
# JLegal Restore Script
# Restores from a backup archive

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup-file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="/tmp/jlegal_restore_$$"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"

# Extract backup
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
BACKUP_NAME=$(ls "$RESTORE_DIR")

# Stop services
echo "Stopping services..."
docker-compose stop api worker beat

# Restore database
echo "Restoring database..."
docker-compose exec -T db psql -U jlegal -d jlegal < "$RESTORE_DIR/$BACKUP_NAME/database.sql"

# Restore storage
echo "Restoring documents..."
docker cp "$RESTORE_DIR/$BACKUP_NAME/storage" $(docker-compose ps -q api):/app/

# Restart services
echo "Restarting services..."
docker-compose up -d

# Cleanup
rm -rf "$RESTORE_DIR"

echo "Restore complete!"
