#!/usr/bin/env bash
# EC2 launch template user-data: bootstraps a brand-new instance in an Auto
# Scaling Group so it is fully in-service before the ALB starts sending it
# traffic (the ALB health check hits /health, see deploy/nginx/commerceos.conf).
set -euo pipefail

export REPO_URL="git@github.com:YOUR_GITHUB_ORG/commerceos.git"
export BRANCH="main"

curl -fsSL https://raw.githubusercontent.com/YOUR_GITHUB_ORG/commerceos/main/deploy/ec2/bootstrap.sh -o /tmp/bootstrap.sh
chmod +x /tmp/bootstrap.sh
/tmp/bootstrap.sh

bash /opt/commerceos/deploy/scripts/migrate.sh
systemctl start commerceos-api
systemctl start commerceos-web
