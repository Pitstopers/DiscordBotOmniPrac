#!/usr/bin/env bash

set -euo pipefail

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
FOLDER="/home/ubuntu/omni-backups"
SOURCE="$HOME/DiscordBotOmniPrac/practice_logs.db"
BACKUP="${FOLDER}/practice_logs-${TIMESTAMP}.db"

if [[ ! -s "$SOURCE" ]]; then
    echo "ERROR: Source database not found or empty!"
    exit 1
fi

mkdir -p "$FOLDER"
chmod 700 "$FOLDER"

sqlite3 "$SOURCE" ".backup '$BACKUP'"

RESULT=$(sqlite3 "$BACKUP" "PRAGMA integrity_check;")

if [[ "$RESULT" != "ok" ]]; then
    echo "ERROR: Backup failed integrity check: $RESULT"
    exit 1
fi
echo "Backup integrity verified successfully!"

aws s3 cp "$BACKUP" \
    "s3://omni-bot-backups/backups/" \
    --region us-east-2
echo "Backup uploaded to Amazon S3 successfully!"
echo "Backup file: $BACKUP"