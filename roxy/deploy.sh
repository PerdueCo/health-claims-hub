#!/bin/bash
set -e

ML_HOST="${ML_HOST:-ml}"
ML_PORT="${ML_PORT:-8002}"
ML_USER="${ML_USERNAME:-admin}"
ML_PASS="${ML_PASSWORD:-admin123}"
WORKDIR="/work/claims-roxy"

# Maximum wait time for MarkLogic to become ready.
# 60 attempts x 10 seconds = 10 minutes maximum.
# Generous enough for slow machines but still fails clearly if something is broken.
MAX_TRIES=60
INTERVAL=10

echo "================================================"
echo " Roxy Deploy Script"
echo " Target: http://$ML_HOST:$ML_PORT"
echo " Max wait: $((MAX_TRIES * INTERVAL / 60)) minutes"
echo "================================================"

echo "[1/4] Waiting for MarkLogic to be ready..."
COUNT=0
until curl -sf --digest -u "$ML_USER:$ML_PASS" \
    "http://$ML_HOST:$ML_PORT/manage/v2?view=status&format=json" > /dev/null 2>&1; do
  COUNT=$((COUNT + 1))
  if [ $COUNT -ge $MAX_TRIES ]; then
    echo ""
    echo "ERROR: MarkLogic did not respond after $((MAX_TRIES * INTERVAL)) seconds."
    echo "  Check: docker ps              — is the ml container running?"
    echo "  Check: docker logs ml         — any startup errors?"
    echo "  Check: docker stats ml        — is the container out of memory?"
    exit 1
  fi
  ELAPSED=$((COUNT * INTERVAL))
  echo "  Waiting... ${ELAPSED}s / $((MAX_TRIES * INTERVAL))s"
  sleep $INTERVAL
done
echo "  MarkLogic is ready ($((COUNT * INTERVAL))s)."

cd "$WORKDIR"

echo "[2/4] Running: ml local bootstrap"
ml local bootstrap || { echo "ERROR: bootstrap failed"; exit 1; }
echo "  Bootstrap complete."

echo "[3/4] Running: ml local deploy modules"
ml local deploy modules || { echo "ERROR: deploy modules failed"; exit 1; }
echo "  Modules deployed."

echo "[4/4] Running: ml local deploy content"
ml local deploy content || { echo "ERROR: deploy content failed"; exit 1; }
echo "  Content deployed."

echo "================================================"
echo " Roxy deploy COMPLETE"
echo " REST server should now be available on port 8040"
echo "================================================"
