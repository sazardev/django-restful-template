#!/bin/bash
# ============================================================================
# BACKUP CRON SERVICE
# ============================================================================

set -e

# Configuration
CRON_SCHEDULE=${BACKUP_SCHEDULE:-"0 2 * * *"}
LOG_FILE="/logs/backup-cron.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create crontab
cat > /tmp/crontab << EOF
$CRON_SCHEDULE /scripts/postgres-backup.sh >> $LOG_FILE 2>&1
0 3 * * 0 /scripts/media-backup.sh >> $LOG_FILE 2>&1
EOF

log "Starting backup service with schedule: $CRON_SCHEDULE"
log "Logs will be written to: $LOG_FILE"

# Start crond in foreground
exec supercronic /tmp/crontab
