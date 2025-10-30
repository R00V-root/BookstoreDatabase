#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 1
fi

FILE=$1

gzip -dc "$FILE" | docker-compose exec -T db psql -U "${POSTGRES_USER:-bookstore}" "${POSTGRES_DB:-bookstore}"
echo "Restore completed from ${FILE}"
