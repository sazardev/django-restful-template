#!/bin/bash
# ============================================================================
# MEDIA FILES BACKUP SCRIPT
# ============================================================================

set -e

# Configuration
BACKUP_DIR="/backups"
MEDIA_DIR="/app/media"
LOG_FILE="/logs/backup.log"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting media files backup..."

# Check if media directory exists
if [ ! -d "$MEDIA_DIR" ]; then
    log "WARNING: Media directory $MEDIA_DIR does not exist, skipping backup"
    exit 0
fi

# Create backup
if tar -czf "$BACKUP_FILE" -C "$MEDIA_DIR" .; then
    log "Media backup created successfully: $BACKUP_FILE"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Media backup size: $BACKUP_SIZE"
    
    # Create latest symlink
    ln -sf "$BACKUP_FILE" "$BACKUP_DIR/latest_media_backup.tar.gz"
    
else
    log "ERROR: Media backup failed!"
    exit 1
fi

# Clean old backups
log "Cleaning media backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "media_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
log "Old media backups cleaned"

# Upload to S3 if configured
if [ "$AWS_S3_BUCKET" ]; then
    log "Uploading media backup to S3..."
    if aws s3 cp "$BACKUP_FILE" "s3://$AWS_S3_BUCKET/backups/media/"; then
        log "Media backup uploaded to S3 successfully"
    else
        log "WARNING: Failed to upload media backup to S3"
    fi
fi

log "Media backup completed successfully"
