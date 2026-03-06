#!/bin/bash
# ================================================
#  MECP Platform Verification Script
#  MarkLogic Enterprise Claims Platform
#  Usage: chmod +x verify.sh && ./verify.sh
# ================================================

HOST="http://localhost:8040"
CREDS="admin:admin"
PASS=0
FAIL=0

# ── Colors ──────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Check function ───────────────────────────────
check() {
  local label="$1"
  local url="$2"
  local method="${3:-GET}"
  local data="$4"
  local expected="${5:-200}"

  if [ "$method" = "POST" ]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      -u "$CREDS" \
      -X POST \
      -H "Content-Type: application/x-www-form-urlencoded" \
      --data-urlencode "$data" \
      "$url")
  else
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      -u "$CREDS" \
      "$url")
  fi

  if [ "$STATUS" = "$expected" ]; then
    echo -e "${GREEN}[PASS]${NC} $label"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}[FAIL]${NC} $label  (expected $expected, got $STATUS)"
    FAIL=$((FAIL + 1))
  fi
}

# ── Header ───────────────────────────────────────
echo ""
echo -e "${BLUE}========================================"
echo " MECP Platform Verification"
echo " MarkLogic Enterprise Claims Platform"
echo -e "========================================${NC}"
echo ""

# ── Tests ────────────────────────────────────────

# 1. REST server alive
check \
  "MarkLogic REST server (port 8040) is responding" \
  "$HOST/v1/ping"

# 2. Claims list endpoint
check \
  "GET /v1/resources/claims returns HTTP 200" \
  "$HOST/v1/resources/claims"

# 3. Status filter — PAID
check \
  "GET /v1/resources/claims?rs:status=PAID returns results" \
  "$HOST/v1/resources/claims?rs:status=PAID"

# 4. Status filter — DENIED
check \
  "GET /v1/resources/claims?rs:status=DENIED returns results" \
  "$HOST/v1/resources/claims?rs:status=DENIED"

# 5. Status filter — PENDING
check \
  "GET /v1/resources/claims?rs:status=PENDING returns results" \
  "$HOST/v1/resources/claims?rs:status=PENDING"

# 6. cts:estimate — document count
check \
  "POST /v1/eval — cts:estimate returns document count" \
  "$HOST/v1/eval" \
  "POST" \
  "xquery=cts:estimate(cts:true-query())"

# 7. Status frequency query
check \
  "POST /v1/eval — status frequency query returns values" \
  "$HOST/v1/eval" \
  "POST" \
  'xquery=for $v in cts:values(cts:element-reference(xs:QName("status"))) return concat($v, ": ", cts:frequency($v))'

# ── Summary ──────────────────────────────────────
echo ""
echo -e "${BLUE}========================================${NC}"

TOTAL=$((PASS + FAIL))

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN} Result: $PASS PASSED  |  $FAIL FAILED${NC}"
  echo -e "${GREEN} Platform is READY for demonstration${NC}"
else
  echo -e "${YELLOW} Result: $PASS PASSED  |  ${RED}$FAIL FAILED${NC}"
  echo ""
  echo -e "${YELLOW} Troubleshooting:${NC}"
  echo "   1. Check Docker is running:  docker ps"
  echo "   2. Check MarkLogic started:  http://localhost:8001"
  echo "   3. Check credentials in this script match your admin setup"
  echo "   4. See README.md for full troubleshooting guide"
fi

echo -e "${BLUE}========================================${NC}"
echo ""
