#!/bin/bash
# ============================================================================
# DATABASE BACKUP SCRIPT
# ============================================================================

set -e

# Configuration
BACKUP_DIR="/backups"
LOG_FILE="/logs/backup.log"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Database configuration
DB_NAME=${POSTGRES_DB}
DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql.gz"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting PostgreSQL backup..."

# Set password for pg_dump
export PGPASSWORD="$DB_PASSWORD"

# Create backup
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose --no-owner --no-privileges | gzip > "$BACKUP_FILE"; then
    log "Backup created successfully: $BACKUP_FILE"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup size: $BACKUP_SIZE"
    
    # Create latest symlink
    ln -sf "$BACKUP_FILE" "$BACKUP_DIR/latest_backup.sql.gz"
    
    # Write last backup info
    echo "{\"timestamp\": \"$(date -Iseconds)\", \"file\": \"$BACKUP_FILE\", \"size\": \"$BACKUP_SIZE\"}" > "$BACKUP_DIR/last_backup.log"
    
else
    log "ERROR: Backup failed!"
    exit 1
fi

# Clean old backups
log "Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "postgres_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
log "Old backups cleaned"

# Upload to S3 if configured
if [ "$AWS_S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    if aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BUCKET/backups/postgres/"; then
        log "Backup uploaded to S3 successfully"
    else
        log "WARNING: Failed to upload backup to S3"
    fi
fi

log "PostgreSQL backup completed successfully"
