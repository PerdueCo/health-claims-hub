"""
Sprint 0 Local Verification Script
Run this BEFORE pushing to GitHub.
Checks every fix made this session is actually in place locally.

Usage:
    python sprint0_verify.py

All checks must show PASS before you run git push.
"""

import os, sys, json, subprocess
from pathlib import Path

ROOT    = Path(__file__).parent
PASSED  = []
FAILED  = []
WARNED  = []

GRN  = "\033[92m"
RED  = "\033[91m"
YLW  = "\033[93m"
BLU  = "\033[94m"
BOLD = "\033[1m"
RST  = "\033[0m"

def header(title):
    print(f"\n{BLU}{BOLD}{'='*55}{RST}")
    print(f"{BLU}{BOLD}  {title}{RST}")
    print(f"{BLU}{BOLD}{'='*55}{RST}")

def ok(label, detail=""):
    PASSED.append(label)
    d = f"  {detail}" if detail else ""
    print(f"  {GRN}PASS{RST}  {label}{d}")

def fail(label, detail=""):
    FAILED.append(label)
    d = f"\n        {RED}→ {detail}{RST}" if detail else ""
    print(f"  {RED}FAIL{RST}  {label}{d}")

def warn(label, detail=""):
    WARNED.append(label)
    d = f"\n        {YLW}→ {detail}{RST}" if detail else ""
    print(f"  {YLW}WARN{RST}  {label}{d}")

def check_file(rel, label=None):
    p = ROOT / rel
    lbl = label or str(rel)
    if p.exists():
        ok(lbl)
        return True
    else:
        fail(lbl, f"Missing: {rel}")
        return False

def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""

# ─────────────────────────────────────────────────────────────
header("1. CORE PLATFORM FILES")
# ─────────────────────────────────────────────────────────────
check_file("docker-compose.yml")
check_file("roxy/Dockerfile")
check_file("claims-roxy/src/app/claims.xqy")
check_file("corb/transform.xqy")
check_file("corb/selector.xqy")
check_file("scripts/run_pipeline.py")
check_file("scripts/generate_claims.py")

# ─────────────────────────────────────────────────────────────
header("2. SPRINT 0 NEW FILES — must exist before push")
# ─────────────────────────────────────────────────────────────
check_file("serve_dashboard.py",    "serve_dashboard.py")
check_file("dashboard.html",        "dashboard.html")
check_file("QUICKSTART.md",         "QUICKSTART.md")
check_file("fix_all.py",            "fix_all.py")
check_file("tests/test_mecp.py",    "tests/test_mecp.py")
check_file("tests/pre_push_check.ps1", "tests/pre_push_check.ps1")

# React dashboard
check_file("dashboard/package.json",                     "dashboard/package.json")
check_file("dashboard/public/index.html",                "dashboard/public/index.html")
check_file("dashboard/src/App.jsx",                      "dashboard/src/App.jsx")
check_file("dashboard/src/index.js",                     "dashboard/src/index.js")
check_file("dashboard/src/services/claimsApi.js",        "dashboard/src/services/claimsApi.js")
check_file("dashboard/src/services/agentService.js",     "dashboard/src/services/agentService.js")
check_file("dashboard/src/hooks/useClaims.js",           "dashboard/src/hooks/useClaims.js")
check_file("dashboard/src/components/Sidebar.jsx",       "dashboard/src/components/Sidebar.jsx")
check_file("dashboard/src/components/KpiCards.jsx",      "dashboard/src/components/KpiCards.jsx")
check_file("dashboard/src/components/ClaimsTable.jsx",   "dashboard/src/components/ClaimsTable.jsx")
check_file("dashboard/src/components/AgentChatPanel.jsx","dashboard/src/components/AgentChatPanel.jsx")
check_file("dashboard/src/components/AgentSessionPanel.jsx","dashboard/src/components/AgentSessionPanel.jsx")
check_file("dashboard/src/pages/Dashboard.jsx",          "dashboard/src/pages/Dashboard.jsx")

# ─────────────────────────────────────────────────────────────
header("3. XQUERY BUG FIXES — confirm correct content")
# ─────────────────────────────────────────────────────────────

claims_xqy = read("claims-roxy/src/app/claims.xqy")
if "cts:json-property-value-query" in claims_xqy:
    ok("claims.xqy uses json-property-value-query (JSON filter fixed)")
else:
    fail("claims.xqy JSON filter NOT fixed",
         "Still uses element-value-query — status filter returns wrong data")

if 'cts:element-value-query(xs:QName("status")' not in claims_xqy:
    ok("claims.xqy old element-value-query removed")
else:
    fail("claims.xqy still has old element-value-query")

if ":= 2000" in claims_xqy or ":= 2000" in claims_xqy:
    ok("claims.xqy default limit is 2000")
elif ":= 100" in claims_xqy:
    fail("claims.xqy default limit still 100", "Dashboard will show truncated data")
else:
    warn("claims.xqy limit value unclear — check manually")

if "cts:estimate" in claims_xqy:
    ok("claims.xqy uses cts:estimate for real total count")
else:
    warn("claims.xqy total count may still use fn:count (less accurate)")

transform_xqy = read("corb/transform.xqy")
if "object-node" in transform_xqy or "xdmp:node-kind" in transform_xqy:
    ok("transform.xqy has JSON guard (prevents CORB crash on XML)")
else:
    fail("transform.xqy missing JSON guard",
         "CORB will crash on triplestore XML docs — add empty($doc/object-node()) check")

selector_xqy = read("corb/selector.xqy")
if 'cts:directory-query("/claims/"' in selector_xqy:
    ok("selector.xqy scoped to /claims/ directory only")
else:
    fail("selector.xqy not scoped to /claims/",
         "CORB will process triplestore XML and crash")

# ─────────────────────────────────────────────────────────────
header("4. DASHBOARD HTML FIX")
# ─────────────────────────────────────────────────────────────

dashboard_html = read("dashboard.html")
if "limit=1000" in dashboard_html or "limit=2000" in dashboard_html:
    ok("dashboard.html API call includes limit parameter")
else:
    fail("dashboard.html missing limit parameter",
         "Dashboard will only show 100 claims — add ?limit=1000 to API call")

if "const API = '/api/v1/resources/claims';" not in dashboard_html:
    ok("dashboard.html does not use bare API call without limit")
else:
    fail("dashboard.html still has bare API call with no limit")

# ─────────────────────────────────────────────────────────────
header("5. run_pipeline.py DUPLICATE FUNCTION CHECK")
# ─────────────────────────────────────────────────────────────

pipeline = read("scripts/run_pipeline.py")
step1_count = pipeline.count("def step1(")
step2_count = pipeline.count("def step2(")

if step1_count == 1:
    ok("run_pipeline.py — step1() defined once")
else:
    fail(f"run_pipeline.py — step1() defined {step1_count} times",
         "Delete the duplicate definition — second one overwrites the first")

if step2_count == 1:
    ok("run_pipeline.py — step2() defined once")
else:
    fail(f"run_pipeline.py — step2() defined {step2_count} times",
         "Delete the duplicate definition")

# ─────────────────────────────────────────────────────────────
header("6. .gitignore — protect node_modules")
# ─────────────────────────────────────────────────────────────

gitignore = read(".gitignore")
if "node_modules" in gitignore:
    ok(".gitignore excludes node_modules")
else:
    fail(".gitignore missing node_modules",
         'Add line: dashboard/node_modules/')

if "dashboard/build" in gitignore or "build/" in gitignore:
    ok(".gitignore excludes dashboard/build")
else:
    warn(".gitignore may not exclude dashboard/build — add dashboard/build/")

# ─────────────────────────────────────────────────────────────
header("7. JUNK FILES — should NOT be in repo")
# ─────────────────────────────────────────────────────────────

junk = [
    "tmp-unique.js",
    "run-roxy-tests.ps1",
    "verify-20260301-055141.txt",
    "health_claims_hub_verify.py",
]
for f in junk:
    p = ROOT / f
    if p.exists():
        warn(f"{f} still exists locally",
             f"Run: git rm {f}  (remove from repo tracking)")
    else:
        ok(f"{f} already removed")

# ─────────────────────────────────────────────────────────────
header("8. BULK CLAIMS DATA")
# ─────────────────────────────────────────────────────────────

bulk = ROOT / "data" / "bulk-claims"
if bulk.exists():
    jsons = list(bulk.glob("*.json"))
    if len(jsons) >= 1000:
        ok(f"data/bulk-claims/ has {len(jsons)} claim files")
    elif len(jsons) > 0:
        warn(f"data/bulk-claims/ only has {len(jsons)} files",
             "Run: python scripts/generate_claims.py")
    else:
        fail("data/bulk-claims/ is empty",
             "Run: python scripts/generate_claims.py")
else:
    fail("data/bulk-claims/ folder missing",
         "Run: python scripts/generate_claims.py")

# ─────────────────────────────────────────────────────────────
header("9. DOCKER — is MarkLogic running?")
# ─────────────────────────────────────────────────────────────

try:
    r = subprocess.run(
        ["docker", "ps", "--filter", "name=ml", "--filter",
         "status=running", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=5
    )
    if "ml" in r.stdout:
        ok("Docker — MarkLogic container 'ml' is running")

        # Quick API check
        import urllib.request, urllib.error
        req = urllib.request.Request(
            "http://localhost:8040/v1/resources/claims?limit=1",
            headers={"Authorization": "Basic YWRtaW46YWRtaW4xMjM="}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            total = data.get("total", 0)
            count = len(data.get("claims", []))
            if total >= 1000:
                ok(f"MarkLogic API — returns total={total} (full dataset)")
            elif total > 0:
                warn(f"MarkLogic API — total={total} (expected 1000+)",
                     "Run: python scripts/run_pipeline.py to load all claims")
            else:
                fail("MarkLogic API — total=0, no claims in database",
                     "Run: python scripts/run_pipeline.py")

            # Status filter test
            req2 = urllib.request.Request(
                "http://localhost:8040/v1/resources/claims?status=PAID&limit=2000",
                headers={"Authorization": "Basic YWRtaW46YWRtaW4xMjM="}
            )
            resp2 = urllib.request.urlopen(req2, timeout=8)
            data2 = json.loads(resp2.read())
            claims2 = data2.get("claims", [])
            bad = [c for c in claims2 if c.get("status") != "PAID"]
            if not claims2:
                warn("Status filter (PAID) returned 0 claims",
                     "Filter may not be working — check claims.xqy in MarkLogic modules")
            elif len(bad) == 0:
                ok(f"Status filter PAID — returns {len(claims2)} claims, all correct status")
            else:
                fail(f"Status filter BROKEN — {len(bad)} non-PAID claims in PAID results",
                     "Upload fixed claims.xqy: run python fix_all.py")

        except Exception as e:
            fail("MarkLogic API not responding on port 8040", str(e)[:80])
    else:
        warn("MarkLogic container not running",
             "Start with: docker compose up -d  (wait 2-3 min then re-run this script)")
except FileNotFoundError:
    warn("Docker not found in PATH",
         "Install Docker Desktop or start it if already installed")
except Exception as e:
    warn(f"Docker check skipped: {e}")

# ─────────────────────────────────────────────────────────────
header("10. SERVE_DASHBOARD.PY — proxy content check")
# ─────────────────────────────────────────────────────────────

proxy = read("serve_dashboard.py")
if "ML_HOST" in proxy and "8040" in proxy:
    ok("serve_dashboard.py configured for port 8040")
else:
    fail("serve_dashboard.py may be misconfigured — check ML_HOST and port")

if "8888" in proxy:
    ok("serve_dashboard.py serves on port 8888")
else:
    warn("serve_dashboard.py port 8888 not found — check PORT setting")

if "/api/" in proxy:
    ok("serve_dashboard.py proxies /api/ prefix correctly")
else:
    fail("serve_dashboard.py missing /api/ proxy route")

# ─────────────────────────────────────────────────────────────
# FINAL REPORT
# ─────────────────────────────────────────────────────────────
total = len(PASSED) + len(FAILED) + len(WARNED)
print(f"\n{BOLD}{'='*55}{RST}")
print(f"{BOLD}  SPRINT 0 LOCAL VERIFICATION RESULT{RST}")
print(f"{BOLD}{'='*55}{RST}")
print(f"  {GRN}PASSED : {len(PASSED)}{RST}")
print(f"  {YLW}WARNED : {len(WARNED)}{RST}")
print(f"  {RED}FAILED : {len(FAILED)}{RST}")
print(f"  Total  : {total} checks")
print()

if FAILED:
    print(f"{RED}{BOLD}  ✗ NOT READY TO PUSH — fix failures first:{RST}")
    for f in FAILED:
        print(f"    {RED}•{RST} {f}")
    print()
    print(f"  Fix all FAIL items, then re-run this script.")
elif WARNED:
    print(f"{YLW}{BOLD}  ⚠ READY TO PUSH WITH WARNINGS{RST}")
    print(f"  Warnings are non-blocking but review before Sprint 1.")
    print()
    print(f"{GRN}{BOLD}  Next steps:{RST}")
    print(f"    1. git add dashboard/ tests/ serve_dashboard.py dashboard.html QUICKSTART.md fix_all.py .gitignore")
    print(f"    2. git add claims-roxy/src/app/claims.xqy corb/transform.xqy corb/selector.xqy")
    print(f"    3. git add scripts/run_pipeline.py")
    print(f"    4. git commit -m 'Sprint 0 — stabilize platform, add React dashboard and test suite'")
    print(f"    5. git push origin main")
else:
    print(f"{GRN}{BOLD}  ✓ ALL CHECKS PASSED — SAFE TO PUSH{RST}")
    print()
    print(f"{GRN}{BOLD}  Next steps:{RST}")
    print(f"    1. git add dashboard/ tests/ serve_dashboard.py dashboard.html QUICKSTART.md fix_all.py .gitignore")
    print(f"    2. git add claims-roxy/src/app/claims.xqy corb/transform.xqy corb/selector.xqy")
    print(f"    3. git add scripts/run_pipeline.py")
    print(f"    4. git commit -m 'Sprint 0 — stabilize platform, add React dashboard and test suite'")
    print(f"    5. git push origin main")

print(f"{BOLD}{'='*55}{RST}\n")
sys.exit(0 if not FAILED else 1)
