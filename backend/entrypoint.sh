#!/bin/sh

set -e  # blow up on any error

# ------------------------------------------------------------
# Если запущены от root, фиксим права и переключаемся на appuser
# ------------------------------------------------------------
if [ "$(id -u)" = "0" ]; then
    echo "[entrypoint] Running as root, fixing /shared permissions..."
    chmod 1777 /shared

    # Перезапускаем этот же скрипт, но от пользователя appuser
    # Все переданные аргументы (например, команда gunicorn) сохраняются
    exec gosu appuser "$0" "$@"
fi

# Дальше всё выполняется от appuser
# ------------------------------------------------------------

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

log()  { echo "${GREEN}[entrypoint]${NC} $1"; }
warn() { echo "${YELLOW}[entrypoint]${NC} $1"; }
err()  { echo "${RED}[entrypoint]${NC} $1" >&2; }

# Waiting for Neo4j

log "Waiting for Neo4j at ${NEO4J_BOLT_URL}"

MAX_RETRIES=30
RETRY_INTERVAL=3
retries=0

until python -c "
import sys
from neomodel import db, config

config.DATABASE_URL = '${NEO4J_BOLT_URL}'
try:
    db.cypher_query('RETURN 1')
    print('Neo4j is ready')
except Exception as e:
    print(f'Not ready: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$MAX_RETRIES" ]; then
        err "Neo4j did not become ready after $((MAX_RETRIES * RETRY_INTERVAL)) seconds. Exiting."
        exit 1
    fi
    warn "Neo4j not ready yet. Retry $retries/$MAX_RETRIES in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
done

log "Neo4j is ready."

# Django migrations (SQLite)

log "Running Django migrations..."
python manage.py migrate --noinput

# Neomodel (indexes, constraints)

log "Installing neomodel labels and constraints..."
neomodel_install_labels apps.pages.models

log "Ensuring custom Neo4j indexes (fulltext, etc.)..."
python manage.py ensure_indexes

# Seed DB

if python manage.py help seed > /dev/null 2>&1; then
    log "Running seed..."
    python manage.py seed
else
    warn "Seed command not found yet — skipping. (Will be added in BE-5)"
fi

# Gunicorn

log "Starting Gunicorn..."
exec gunicorn -c gunicorn.conf.py config.wsgi:application
