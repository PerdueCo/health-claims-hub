# MECP Testing and Verification Guide

Three levels of platform verification plus dashboard testing.
Run these in order on a fresh clone to confirm everything works end to end.

---

## Level 1 — Runtime Verification (2 minutes)

Confirms the platform is running and all endpoints are responding.

**Run:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

**Expected result:**
```
========================================
Result: 6 PASSED | 0 FAILED
Platform is READY for demonstration
========================================
```

**What each check confirms:**

| Check | What It Tests |
|---|---|
| GET /manage/v2 | MarkLogic is running and Manage API responds |
| GET /v1/ping | App Services layer is up |
| GET /v1/resources | Roxy routing is active |
| GET /v1/resources/claims | Claims API returns JSON data |
| POST /v1/eval - count | XQuery execution works, documents are loaded |
| POST /v1/eval - frequency | Range index is active and returning values |

---

## Level 2 — Persistence Verification (5 minutes)

Confirms the platform configuration survives a full teardown and rebuild.

**Run:**
```powershell
docker compose down -v
docker compose up -d
# Wait 60 seconds
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

**Expected result:** 6 PASSED — identical to Level 1.

**What this proves:**
- Range index is declared in ml-config.xml, not just the Admin UI
- Roxy redeploys all 81 modules automatically on every boot
- All 10 seed claim documents reload automatically
- No manual configuration steps required

---

## Level 3 — Portability Verification (15 minutes)

Confirms the platform works on any machine from a fresh clone.

**Run on a different machine or in a new folder:**
```powershell
git clone https://github.com/PerdueCo/health-claims-hub
cd health-claims-hub
docker compose up -d
# Wait 60 seconds
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

**Expected result:** 6 PASSED with zero manual steps.

See [docs/MECP_Setup_Guide.pdf](docs/MECP_Setup_Guide.pdf) for full
step-by-step instructions for a brand-new Windows machine.

---

## Level 4 — Pipeline Verification (3 minutes)

Confirms MLCP bulk load and CORB batch processing work correctly.

**Run:**
```powershell
python scripts\generate_claims.py
python scripts\run_pipeline.py
```

**Expected result:**
```
STEP 1 - Seed documents : 10   Bulk documents : 1000   Total : 1010
STEP 2 - Missing from database : 0
STEP 3 - Skipping MLCP (all loaded)
STEP 4 - 10/10 documents validated
STEP 5 - CORB completed 1010/1010 tasks
STEP 6 - PIPELINE COMPLETE
  Status distribution:
    PAID:    ~500
    DENIED:  ~300
    PENDING: ~200
```

**What this proves:**
- MLCP ingests 1000 JSON documents via Docker
- CORB selector scopes correctly to /claims/ directory only
- 6-step transform pipeline runs without errors
- Pipeline is idempotent — safe to re-run multiple times

---

## Level 5 — Dashboard Verification (2 minutes)

Confirms the live dashboard connects to MarkLogic and displays data.

**Step 1 — Start the dashboard server (in a separate PowerShell window):**
```powershell
python serve_dashboard.py
```

You should see:
```
==================================================
  MECP Dashboard Server
  http://localhost:8888/dashboard.html
  Press Ctrl+C to stop
==================================================
```

**Step 2 — Open Chrome and go to:**
```
http://localhost:8888/dashboard.html
```

**Step 3 — Confirm these 5 things:**

| Check | What To Look For |
|---|---|
| Data loads | KPI cards show numbers, not "Loading..." |
| Status indicator | Top right shows "Live — MarkLogic 11" |
| Filters work | Click Paid / Denied / Pending — table updates |
| Financials load | Total Billed shows a dollar amount |
| Auto-refresh | Timestamp in top right updates every 30 seconds |

**Step 4 — Test error handling:**
```powershell
docker compose down
```
Refresh the dashboard — should show "Connection failed" in red, not crash or go blank.

Bring it back:
```powershell
docker compose up -d
```
Wait 30 seconds, refresh — data returns automatically.

---

## Level 6 — SPARQL Verification (2 minutes)

Confirms semantic triples are loaded and SPARQL queries return correct results.

**Total billed by status:**
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Expected result:**
```
Status: DENIED  | Claims: ~300 | Total Billed: $X,XXX,XXX
Status: PAID    | Claims: ~500 | Total Billed: $X,XXX,XXX
Status: PENDING | Claims: ~200 | Total Billed: $XXX,XXX
```

**PENDING claims by provider:**
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-pending-by-provider.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Expected result:** List of providers with PENDING claims sorted alphabetically.

---

## Quick Reference — All Test Commands

```powershell
# Level 1 - Runtime
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1

# Level 2 - Persistence
docker compose down -v
docker compose up -d
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1

# Level 4 - Pipeline
python scripts\generate_claims.py
python scripts\run_pipeline.py

# Level 5 - Dashboard
python serve_dashboard.py
# open http://localhost:8888/dashboard.html

# Level 6 - SPARQL
curl.exe --digest -u admin:admin123 --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" --data "database=roxy-content" http://localhost:8000/v1/eval
```

---

## Stopping the Platform

```powershell
# Stop containers, keep data
docker compose down

# Stop containers, wipe all data (clean slate for next session)
docker compose down -v
```

---

*MECP Testing Guide — v1.1*
