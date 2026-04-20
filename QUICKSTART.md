# MECP Quick Start Guide

> Get the platform running on a clean machine in under 15 minutes.
> Written for Windows. Every step explained. Nothing assumed.

---

## What You Are About to Set Up

You are setting up a fully containerized MarkLogic 11 enterprise
healthcare claims platform. When complete you will have:

- MarkLogic database running in Docker with 1010 claim documents
- REST API serving live claims data on port 8040
- Live HTML dashboard at http://localhost:8888/dashboard.html
- All 6 verification tests passing

---

## Before You Start — Required Software

You need three things installed. If you already have them skip ahead.

### 1. Docker Desktop
**What it is:** The engine that runs MarkLogic on your machine.
**Must be OPEN and running** before any commands below.

```
Download: https://www.docker.com/products/docker-desktop
Install:  Run the installer, accept all defaults
Restart:  Restart your computer when prompted
Start:    Open Docker Desktop from Start menu
Wait:     Watch for the whale icon in taskbar to show "Engine running"
```

### 2. Git
**What it is:** Downloads the project files from GitHub.

```
Download: https://git-scm.com
Install:  Run the installer, accept all defaults
Verify:   Open PowerShell and type: git --version
Expected: git version 2.x.x
```

### 3. Python 3
**What it is:** Runs the pipeline and dashboard scripts.

```
Download: https://www.python.org/downloads
Install:  Run installer
          CHECK the box that says "Add Python to PATH"
Verify:   Open PowerShell and type: python --version
Expected: Python 3.x.x
```

---

## Step-by-Step Setup

### STEP 1 — Open Docker Desktop

Find Docker Desktop in your Start menu and open it.
Wait until the whale icon in your taskbar stops animating
and shows **Engine running**.

**Do not skip this step.** Every command below requires Docker running.

---

### STEP 2 — Open PowerShell

Press `Windows + X` and click **Windows PowerShell** or **Terminal**.

---

### STEP 3 — Clone the Repository

```powershell
cd "C:\Users\YourName\Documents"
git clone https://github.com/PerdueCo/health-claims-hub
cd health-claims-hub
```

Replace `YourName` with your actual Windows username.

---

### STEP 4 — Start the Platform

```powershell
docker compose up -d
```

**What this does:**
- Downloads the MarkLogic 11 Docker image (2GB — only on first run)
- Creates and starts the MarkLogic container
- Runs Roxy bootstrap to create databases and deploy XQuery modules

**First run time:** 5-10 minutes depending on internet speed.
**Subsequent runs:** 30-60 seconds (image is cached).

---

### STEP 5 — Wait for MarkLogic to Initialize

This is the most important step people skip.

```powershell
docker logs -f health-claims-hub-roxy-1
```

Watch the logs scroll. Wait until you see:

```
Roxy deploy COMPLETE
```

**Do not run the next step until you see this message.**
Press `Ctrl + C` to stop watching logs when ready.

---

### STEP 6 — Verify the Platform

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

**Expected result:**

```
========================================
  MECP Verification
========================================
[PASS] GET /manage/v2 returns status
[PASS] GET /v1/ping returns OK
[PASS] GET /v1/resources returns a response
[PASS] GET /v1/resources/claims returns results
[PASS] POST /v1/eval - cts:estimate returns count
[PASS] POST /v1/eval - status frequency returns values
========================================
Result: 6 PASSED | 0 FAILED
Platform is READY for demonstration
========================================
```

If you see anything other than 6 PASSED go to the
Troubleshooting section at the bottom of this guide.

---

### STEP 7 — Load 1000 Claims

```powershell
python scripts\generate_claims.py
python scripts\run_pipeline.py
```

**What this does:**
- Generates 1000 synthetic JSON claim documents
- Loads them into MarkLogic via MLCP
- Runs 6-step CORB transformation pipeline
- Verifies all 1010 documents processed (10 seed + 1000 bulk)

**Expected output:**

```
STEP 1 - Inspecting database state
STEP 2 - Identifying missing documents
STEP 3 - Loading missing documents via MLCP
STEP 4 - Validating loaded documents     10/10 passed
STEP 5 - Running CORB pipeline           1010/1010 complete
STEP 6 - Final report
  Total documents              : 1010
  Bulk-claims collection       : 1000
  Documents with processedDate : 1010
```

---

### STEP 8 — Start the Dashboard

```powershell
python serve_dashboard.py
```

Open Chrome and go to:
```
http://localhost:8888/dashboard.html
```

You should see the live dashboard with:
- KPI cards showing 1010 total claims
- PAID / DENIED / PENDING distribution
- Financial summary
- Top providers table
- Filter buttons by status

---

## Quick Reference — Commands Summary

```powershell
# Start everything (after Docker Desktop is open)
docker compose up -d

# Watch startup logs — wait for "Roxy deploy COMPLETE"
docker logs -f health-claims-hub-roxy-1

# Verify platform — must show 6 PASSED
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1

# Load 1000 claims
python scripts\generate_claims.py
python scripts\run_pipeline.py

# Start dashboard
python serve_dashboard.py
# Open: http://localhost:8888/dashboard.html

# Stop everything when done
docker compose down
```

---

## Port Reference

| Port | What It Is | How to Access |
|---|---|---|
| 8001 | MarkLogic Admin UI | http://localhost:8001 — login: admin/admin123 |
| 8040 | REST API | curl -u admin:admin123 http://localhost:8040/v1/resources/claims |
| 8888 | Dashboard | http://localhost:8888/dashboard.html |

---

## Troubleshooting

### "docker: command not found" or pipe error
**Cause:** Docker Desktop is not running.
**Fix:** Open Docker Desktop from Start menu. Wait for Engine running.

### "6 PASSED" shows less than 6
**Cause:** MarkLogic is still initializing.
**Fix:** Run `docker logs -f health-claims-hub-roxy-1` and wait for
"Roxy deploy COMPLETE" before running verify again.

### Dashboard shows no data (blank KPI cards)
**Cause:** Pipeline not run yet, or MarkLogic not fully ready.
**Fix:** Run `python scripts\run_pipeline.py` then refresh the dashboard.

### "Cannot connect to server" on curl commands
**Cause:** MarkLogic container not running.
**Fix:** Run `docker ps` to check. If empty run `docker compose up -d`.

### First-time docker compose up takes too long
**Cause:** Downloading the 2GB MarkLogic image.
**Fix:** Be patient. Only happens once. Subsequent starts are fast.

### Port already in use error
**Cause:** Another application using port 8040 or 8888.
**Fix:** Close other applications or restart your machine.

---

## Stopping the Platform

When you are done with your demo:

```powershell
# Stop containers but keep data
docker compose down

# Stop containers AND wipe all data (full reset)
docker compose down -v
```

Use `docker compose down` normally.
Use `docker compose down -v` only if you want to start completely fresh.

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB free | 8 GB free |
| Disk space | 5 GB free | 10 GB free |
| Internet | Required for first run | Not needed after image download |
| OS | Windows 10/11 | Windows 11 |

---

*MarkLogic Enterprise Claims Platform — QUICKSTART.md*
*For full documentation see README.md*
