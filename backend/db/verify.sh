#!/usr/bin/env bash
# Builds the schema in a throwaway PostgreSQL container and runs the smoke tests.
# Usage: backend/db/verify.sh [postgres image tag, default 16]
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tag="${1:-16}"
name="ai-mentor-schema-check-$$"

docker run -d --rm --name "$name" -e POSTGRES_PASSWORD=check -e POSTGRES_DB=mentor "postgres:$tag" >/dev/null
trap 'docker stop "$name" >/dev/null' EXIT

for _ in $(seq 1 60); do
    docker exec "$name" pg_isready -U postgres -d mentor -q && break
    sleep 1
done
sleep 1

run() { docker exec -i "$name" psql -U postgres -d mentor -X -q -v ON_ERROR_STOP=1 "$@"; }

cat "$here"/schema/*.sql | run --single-transaction -f - >/dev/null
echo "schema applied on postgres:$tag"
run -f - < "$here/tests/smoke.sql"
echo "smoke tests passed"
