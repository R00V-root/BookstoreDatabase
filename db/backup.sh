#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
FILE="backup_${TIMESTAMP}.sql.gz"

docker-compose exec -T db pg_dump -U "${POSTGRES_USER:-bookstore}" "${POSTGRES_DB:-bookstore}" | gzip > "${FILE}"
echo "Backup written to ${FILE}"
