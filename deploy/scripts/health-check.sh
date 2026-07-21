#!/usr/bin/env bash
# Polls /ready until it returns 200 or the retry budget is exhausted.
# Used by deploy.sh to confirm a freshly restarted service is actually
# healthy before declaring the rolling deploy successful.
set -euo pipefail

URL="${1:-http://127.0.0.1:8000/ready}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    status=$(curl -s -o /dev/null -w '%{http_code}' "$URL" || echo "000")
    if [ "$status" = "200" ]; then
        echo "Healthy after $attempt attempt(s)."
        exit 0
    fi
    echo "Attempt $attempt/$MAX_ATTEMPTS: got status $status, retrying in ${SLEEP_SECONDS}s..."
    sleep "$SLEEP_SECONDS"
done

echo "Service did not become healthy after $MAX_ATTEMPTS attempts." >&2
exit 1
