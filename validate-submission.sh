#!/usr/bin/env bash
#
# OpenEnv Submission Validator 2026 (Bash Version)
# Usage: ./validate-submission.sh <ping_url> [repo_dir]
#

set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

PING_URL="${1:-}"
REPO_DIR="${2:-.}"

if [ -z "$PING_URL" ]; then
    printf "${RED}Error: Missing URL.${NC}\nUsage: %s <ping_url> [repo_dir]\n" "$0"
    exit 1
fi

log()  { printf "[%s] %b\n" "$(date -u +%H:%M:%S)" "$*"; }
pass() { log "${GREEN}PASSED${NC} -- $1"; }
fail() { log "${RED}FAILED${NC} -- $1"; exit 1; }

printf "${BOLD}========================================\n"
printf "  OpenEnv Submission Validator (Linux)\n"
printf "========================================${NC}\n"

# Step 1: Connectivity Check
log "Step 1/3: Pinging Space at $PING_URL/reset ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d '{}' \
  "$PING_URL/reset" --max-time 15 || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    pass "HF Space is live and responded to /reset"
else
    fail "HF Space /reset returned $HTTP_CODE. Is the Space running?"
fi

# Step 2: Dockerfile Check
log "Step 2/3: Checking for Dockerfile ..."
if [ -f "$REPO_DIR/Dockerfile" ]; then
    pass "Dockerfile found in root."
else
    fail "No Dockerfile found. OpenEnv requires a containerized environment."
fi

# Step 3: OpenEnv CLI Validation
log "Step 3/3: Running openenv validate ..."
if ! command -v openenv &> /dev/null; then
    log "${YELLOW}Warning: 'openenv' CLI not found. Skipping local structural check.${NC}"
    log "Hint: pip install openenv"
else
    if openenv validate "$REPO_DIR" &> /dev/null; then
        pass "openenv validate passed."
    else
        fail "openenv validate failed. Check your openenv.yaml or models.py."
    fi
fi

printf "\n${GREEN}${BOLD}ALL CHECKS PASSED! Your submission is ready.${NC}\n\n"