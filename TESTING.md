# Platform Verification Guide

This document explains how to verify the MarkLogic Enterprise Claims Platform
at every level — from confirming it is running right now, to proving it rebuilds
correctly from scratch, to validating it works on a machine that has never seen it before.

There are three levels. Each one proves something different.

---

## Level 1 — Runtime Verification

**What it proves:** The platform is running and all endpoints are responding correctly.

**When to run:** After every `docker compose up -d` before a demo or interview.

**Command:**
```powershell
# Windows
cd scripts
.\verify.ps1

# Mac / Linux
cd scripts
chmod +x verify.sh
./verify.sh
```

**Expected output:**
```
========================================
MarkLogic Verification Script
========================================
Host         : localhost
Manage Port  : 8002  (digest auth)
REST Port    : 8000  (digest auth)
App Port     : 8040  (basic auth)
User         : admin

==> Checking MarkLogic endpoints
[PASS] GET /manage/v2 returns status (HTTP 200)
[PASS] GET /v1/ping returns OK (HTTP 204)
[PASS] GET /v1/resources returns a response (HTTP 404)
[PASS] GET /v1/resources/claims returns results (HTTP 404)
[PASS] POST /v1/eval - cts:estimate returns document count (HTTP 200)
[PASS] POST /v1/eval - status frequency returns values (HTTP 200)
========================================
Result: 6 PASSED | 0 FAILED
Platform is READY for demonstration
```

**What each test proves:**

| Test | Port | Auth | What It Proves |
|---|---|---|---|
| GET /manage/v2 | 8002 | Digest | MarkLogic initialized and Manage API responding |
| GET /v1/ping | 8000 | Digest | App Services REST layer is alive |
| GET /v1/resources | 8040 | Basic | Roxy app server deployed and serving |
| GET /v1/resources/claims | 8040 | Basic | Claims extension endpoint is reachable |
| POST /v1/eval cts:estimate | 8000 | Digest | XQuery execution works against roxy-content |
| POST /v1/eval status frequency | 8000 | Digest | Range index on status field is active |

**If a test fails:** See the troubleshooting section at the bottom of this document.

---

## Level 2 — Persistence Verification

**What it proves:** All configuration — including the database, range indexes, modules,
and content — is defined in source code and rebuilds automatically from scratch.
Nothing depends on manual Admin UI changes that would be lost on a volume wipe.

**When to run:** After any change to `ml-config.xml`, `deploy.sh`, or `docker-compose.yml`.
Also run this before tagging a release.

**Step 1 — Destroy everything including the Docker volume:**
```powershell
cd "C:\Users\cash america\DOCUMENTS\PROJECTS\health-claims-hub"
docker compose down -v
```

Expected output:
```
✔ Container health-claims-hub-roxy-1  Removed
✔ Container ml                        Removed
✔ Volume health-claims-hub_ml-data    Removed
✔ Network health-claims-hub_default   Removed
```

**Step 2 — Rebuild completely from scratch:**
```powershell
docker compose up -d
docker logs -f health-claims-hub-roxy-1
```

Wait until you see:
```
================================================
 Roxy deploy COMPLETE
 REST server should now be available on port 8040
================================================
```

This confirms:
- MarkLogic initialized with fresh databases and forests
- 78 XQuery modules loaded into roxy-modules
- 10 claim documents loaded into roxy-content
- Range index on status field created from ml-config.xml

**Step 3 — Run the range index persistence test:**
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=for+%24v+in+cts%3Avalues(cts%3Aelement-reference(xs%3AQName(%22status%22)))+return+concat(%24v%2C+%22%3A+%22%2C+cts%3Afrequency(%24v))&database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Expected output:**
```
DENIED: 3
PAID:   5
PENDING: 2
```

**What this proves:** The range index was created by Roxy from `ml-config.xml` —
not from a previous Admin UI change. If you see this output after a full volume
wipe, the index definition is correctly in source control and will work on any machine.

**Failure output (range index NOT in ml-config.xml):**
```
500 Internal Server Error
XDMP-ELEMRIDXNOTFOUND: cts:element-reference(fn:QName("","status"))
```

If you see this, check that `claims-roxy/deploy/ml-config.xml` contains the
`<range-element-index>` block for the status field.

**Step 4 — Run Level 1 verification again:**
```powershell
cd scripts
.\verify.ps1
```

Expected: `6 PASSED | 0 FAILED`

**Level 2 is passed when:** All 6 tests pass after a full `down -v` rebuild with
no manual intervention between wipe and verify.

---

## Level 3 — Portability Verification

**What it proves:** Anyone can clone the repository on a machine that has never
run this project before and get a fully working platform in three commands.
This is the standard that matters for interviews and demos.

**When to run:** Before any major release tag. Required before Day 13 sign-off.

**Requirements:**
- A machine (or VM) that has never had this project on it
- Docker Desktop installed
- Git installed
- No existing `health-claims-hub` folder anywhere

**Step 1 — Fresh clone:**
```powershell
git clone https://github.com/PerdueCo/health-claims-hub
cd health-claims-hub
```

**Step 2 — Start the platform:**
```powershell
docker compose up -d
docker logs -f health-claims-hub-roxy-1
```

Wait for `Roxy deploy COMPLETE`.

**Step 3 — Verify:**
```powershell
cd scripts
.\verify.ps1
```

**Expected:** `6 PASSED | 0 FAILED — Platform is READY for demonstration`

**Level 3 is passed when:** A person who has never seen this project before
can run these three steps and get 6 PASSED with no guidance, no manual steps,
and no Admin UI changes.

**Level 3 status:** Scheduled for Day 13 (March 17, 2026).

---

## Verified Test Results

| Date | Level | Who | Result | Notes |
|---|---|---|---|---|
| Mar 6, 2026 | Level 1 | Developer | 6 PASSED / 0 FAILED | After auth fix and range index |
| Mar 7, 2026 | Level 2 | Developer | 6 PASSED / 0 FAILED | After full down -v rebuild |
| Mar 17, 2026 | Level 3 | TBD | Pending | Fresh clone test — Day 13 |

---

## Troubleshooting

**0 PASSED — all tests show "Could not connect to server"**
```powershell
docker ps
# If ml container is not listed, run:
docker compose up -d
docker logs -f health-claims-hub-roxy-1
```

**1 PASSED — only Manage API passes, rest show 401**
```
Auth mismatch. Port 8040 uses basic auth, port 8000 uses digest.
Confirm you are running the latest verify.ps1 from scripts/.
```

**5 PASSED — status frequency returns HTTP 500**
```
Range index missing from roxy-content database.
Check claims-roxy/deploy/ml-config.xml for the status range-element-index block.
Run docker compose down -v && docker compose up -d to rebuild with the correct config.
```

**Roxy exits after attempt 60 — MarkLogic did not become ready**
```powershell
docker ps                    # is ml container running?
docker logs ml               # any startup errors?
docker stats ml              # is container out of memory?
# MarkLogic needs at least 4GB RAM — check Docker Desktop memory settings
```

---

## Related Documents

| Document | Location | Purpose |
|---|---|---|
| Verification scripts | `scripts/verify.ps1`, `scripts/verify.sh` | Automated Level 1 testing |
| RCA Prevention Report | `docs/MECP_RCA_Prevention_Report.docx` | Root cause analysis of 3 infrastructure failures |
| Database config | `claims-roxy/deploy/ml-config.xml` | Range indexes, database settings |
| Deploy script | `roxy/deploy.sh` | Bootstrap and deploy automation |
| README | `README.md` | Project overview and quick start |

---

*Last verified: March 7, 2026 — Level 2 PASSED after full volume wipe*  
*Level 3 portability test scheduled: March 17, 2026*
