#!/usr/bin/env bash
# Triggers an on-demand RDS snapshot. RDS also takes automated daily snapshots
# per its configured backup window/retention — this script is for pre-deploy
# or ad-hoc backups on top of that. Requires the caller's IAM identity to have
# rds:CreateDBSnapshot on the target instance.
set -euo pipefail

DB_INSTANCE_IDENTIFIER="${DB_INSTANCE_IDENTIFIER:-commerceos-production}"
SNAPSHOT_ID="${DB_INSTANCE_IDENTIFIER}-manual-$(date -u +%Y%m%d-%H%M%S)"

echo "==> Creating snapshot $SNAPSHOT_ID of $DB_INSTANCE_IDENTIFIER"
aws rds create-db-snapshot \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --db-snapshot-identifier "$SNAPSHOT_ID"

echo "==> Waiting for snapshot to become available (this can take several minutes)"
aws rds wait db-snapshot-available --db-snapshot-identifier "$SNAPSHOT_ID"

echo "==> Snapshot $SNAPSHOT_ID is available."
