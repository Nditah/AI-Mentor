#!/usr/bin/env bash
# Applies the target schema to an EMPTY database in one transaction.
# Usage: DATABASE_URL=postgresql://owner@host:5432/mentor backend/db/apply.sh
# Run as a login that is a member of mentor_owner (or the server admin on first run).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
url="${DATABASE_URL:?set DATABASE_URL (libpq form, without +psycopg)}"

cat "$here"/schema/*.sql | psql "$url" -X -q -v ON_ERROR_STOP=1 --single-transaction -f -
echo "schema applied"
