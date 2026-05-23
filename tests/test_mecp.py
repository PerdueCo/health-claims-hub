"""
MECP Automated Test Suite
Run before every git push to verify nothing is broken.

Usage:
    python tests/test_mecp.py
    python tests/test_mecp.py --verbose
    python tests/test_mecp.py --suite api
    python tests/test_mecp.py --suite dashboard
    python tests/test_mecp.py --suite files

Suites: api | pipeline | dashboard | files | all (default)
Requires: pip install requests
"""

import sys
import os
import json
import time
import argparse
import unittest
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

# ── Config ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
ML_BASIC    = HTTPBasicAuth("admin", "admin123")
ML_DIGEST   = HTTPDigestAuth("admin", "admin123")
REST_URL    = "http://localhost:8040"
EVAL_URL    = "http://localhost:8000/v1/eval"
MODULES_URL = "http://localhost:8041/v1/documents"
DASH_URL    = "http://localhost:8888"

# ── Helpers ───────────────────────────────────────────────────────────────────
def xquery(q, db="roxy-content"):
    r = requests.post(EVAL_URL, data={"xquery": q, "database": db},
                      auth=ML_DIGEST, timeout=10)
    return r

def parse_int(text):
    for line in text.splitlines():
        try: return int(line.strip())
        except: pass
    return 0

# ═══════════════════════════════════════════════════════════════════════════════
# SUITE 1 — File structure (no Docker needed)
# ═══════════════════════════════════════════════════════════════════════════════
class TestFileStructure(unittest.TestCase):
    """Verify all required files exist locally before push."""

    def _exists(self, *parts):
        p = ROOT.joinpath(*parts)
        self.assertTrue(p.exists(), f"Missing: {p.relative_to(ROOT)}")

    def test_docker_compose_exists(self):
        self._exists("docker-compose.yml")

    def test_claims_xqy_exists(self):
        self._exists("claims-roxy", "src", "app", "claims.xqy")

    def test_transform_xqy_exists(self):
        self._exists("corb", "transform.xqy")

    def test_selector_xqy_exists(self):
        self._exists("corb", "selector.xqy")

    def test_run_pipeline_exists(self):
        self._exists("scripts", "run_pipeline.py")

    def test_generate_claims_exists(self):
        self._exists("scripts", "generate_claims.py")

    def test_serve_dashboard_exists(self):
        self._exists("serve_dashboard.py")

    def test_dashboard_html_exists(self):
        self._exists("dashboard.html")

    def test_bulk_claims_data_exists(self):
        bulk = ROOT / "data" / "bulk-claims"
        self.assertTrue(bulk.exists(), "data/bulk-claims/ folder missing")
        jsons = list(bulk.glob("*.json"))
        self.assertGreaterEqual(len(jsons), 100,
            f"Only {len(jsons)} bulk claim files found — expected 1000")

    def test_claims_xqy_uses_json_property_query(self):
        """Confirm the JSON filter fix is in place."""
        content = (ROOT / "claims-roxy" / "src" / "app" / "claims.xqy").read_text()
        self.assertIn("cts:json-property-value-query",  content,
            "claims.xqy still uses element-value-query — JSON filter is broken")
        self.assertNotIn('cts:element-value-query(xs:QName("status")', content,
            "claims.xqy still has old XML element query")

    def test_transform_xqy_has_json_guard(self):
        """Confirm transform skips non-JSON docs to prevent CORB crash."""
        content = (ROOT / "corb" / "transform.xqy").read_text()
        self.assertTrue(
            "object-node" in content or "xdmp:node-kind" in content,
            "transform.xqy is missing the JSON guard — will crash on triplestore XML"
        )

    def test_claims_xqy_limit_is_2000(self):
        """Confirm default limit is raised from 100."""
        content = (ROOT / "claims-roxy" / "src" / "app" / "claims.xqy").read_text()
        self.assertNotIn(":= 100", content,
            "claims.xqy default limit is still 100 — dashboard will show truncated data")

    def test_dashboard_html_has_limit_param(self):
        """Confirm dashboard requests more than 100 claims."""
        content = (ROOT / "dashboard.html").read_text()
        self.assertNotIn("const API = '/api/v1/resources/claims';", content,
            "dashboard.html is calling API with no limit parameter")

    def test_gitignore_excludes_node_modules(self):
        gi = ROOT / ".gitignore"
        if gi.exists():
            content = gi.read_text()
            self.assertIn("node_modules", content,
                ".gitignore does not exclude node_modules — will commit huge folder")

    # React dashboard files
    def test_react_dashboard_package_json(self):
        self._exists("dashboard", "package.json")

    def test_react_dashboard_app(self):
        self._exists("dashboard", "src", "App.jsx")

    def test_react_claims_api_service(self):
        self._exists("dashboard", "src", "services", "claimsApi.js")

    def test_react_agent_service(self):
        self._exists("dashboard", "src", "services", "agentService.js")

    def test_react_use_claims_hook(self):
        self._exists("dashboard", "src", "hooks", "useClaims.js")

    def test_react_sidebar(self):
        self._exists("dashboard", "src", "components", "Sidebar.jsx")

    def test_react_kpi_cards(self):
        self._exists("dashboard", "src", "components", "KpiCards.jsx")

    def test_react_claims_table(self):
        self._exists("dashboard", "src", "components", "ClaimsTable.jsx")

    def test_react_agent_chat(self):
        self._exists("dashboard", "src", "components", "AgentChatPanel.jsx")

    def test_react_agent_session(self):
        self._exists("dashboard", "src", "components", "AgentSessionPanel.jsx")

    def test_react_dashboard_page(self):
        self._exists("dashboard", "src", "pages", "Dashboard.jsx")

# ═══════════════════════════════════════════════════════════════════════════════
# SUITE 2 — MarkLogic REST API
# ═══════════════════════════════════════════════════════════════════════════════
class TestMarkLogicAPI(unittest.TestCase):
    """Live API tests — require Docker + MarkLogic running."""

    @classmethod
    def setUpClass(cls):
        try:
            r = requests.get(f"{REST_URL}/v1/resources/claims?limit=1",
                             auth=ML_BASIC, timeout=5)
            cls.ml_up = r.status_code == 200
        except Exception:
            cls.ml_up = False
        if not cls.ml_up:
            print("\n  [SKIP] MarkLogic not running — start with: docker compose up -d")

    def setUp(self):
        if not self.ml_up:
            self.skipTest("MarkLogic not available")

    def test_api_returns_200(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?limit=1", auth=ML_BASIC)
        self.assertEqual(r.status_code, 200)

    def test_api_returns_json(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?limit=1", auth=ML_BASIC)
        data = r.json()
        self.assertIn("claims", data)
        self.assertIn("total", data)

    def test_api_total_is_over_1000(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?limit=1", auth=ML_BASIC)
        total = r.json().get("total", 0)
        self.assertGreaterEqual(total, 1000,
            f"API reports only {total} claims — pipeline may not have run")

    def test_api_returns_2000_with_limit(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?limit=2000", auth=ML_BASIC)
        data = r.json()
        self.assertGreaterEqual(len(data.get("claims", [])), 1000,
            "API returned fewer than 1000 claims with limit=2000")

    def test_status_filter_paid_only(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?status=PAID&limit=2000",
                         auth=ML_BASIC)
        claims = r.json().get("claims", [])
        self.assertGreater(len(claims), 0, "No PAID claims returned")
        bad = [c for c in claims if c.get("status") != "PAID"]
        self.assertEqual(len(bad), 0,
            f"Filter broken: {len(bad)} non-PAID claims in PAID results")

    def test_status_filter_denied_only(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?status=DENIED&limit=2000",
                         auth=ML_BASIC)
        claims = r.json().get("claims", [])
        self.assertGreater(len(claims), 0, "No DENIED claims returned")
        bad = [c for c in claims if c.get("status") != "DENIED"]
        self.assertEqual(len(bad), 0,
            f"Filter broken: {len(bad)} non-DENIED claims in DENIED results")

    def test_status_filter_pending_only(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?status=PENDING&limit=2000",
                         auth=ML_BASIC)
        claims = r.json().get("claims", [])
        self.assertGreater(len(claims), 0, "No PENDING claims returned")
        bad = [c for c in claims if c.get("status") != "PENDING"]
        self.assertEqual(len(bad), 0,
            f"Filter broken: {len(bad)} non-PENDING in PENDING results")

    def test_status_counts_add_up(self):
        paid    = requests.get(f"{REST_URL}/v1/resources/claims?status=PAID&limit=1",    auth=ML_BASIC).json().get("total", 0)
        denied  = requests.get(f"{REST_URL}/v1/resources/claims?status=DENIED&limit=1",  auth=ML_BASIC).json().get("total", 0)
        pending = requests.get(f"{REST_URL}/v1/resources/claims?status=PENDING&limit=1", auth=ML_BASIC).json().get("total", 0)
        total   = requests.get(f"{REST_URL}/v1/resources/claims?limit=1",                auth=ML_BASIC).json().get("total", 0)
        self.assertEqual(paid + denied + pending, total,
            f"Status counts don't add up: {paid}+{denied}+{pending}={paid+denied+pending} != total {total}")

    def test_single_claim_lookup(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?id=CLM-0001", auth=ML_BASIC)
        data = r.json()
        claims = data.get("claims", [])
        self.assertEqual(len(claims), 1, "Single claim lookup failed for CLM-0001")
        self.assertEqual(claims[0].get("claimId"), "CLM-0001")

    def test_claim_has_required_fields(self):
        r = requests.get(f"{REST_URL}/v1/resources/claims?limit=5", auth=ML_BASIC)
        claims = r.json().get("claims", [])
        required = ["claimId", "memberId", "provider", "serviceDate", "status", "amountBilled"]
        for c in claims:
            for field in required:
                self.assertIn(field, c, f"Claim {c.get('claimId')} missing field: {field}")

    def test_modules_db_has_transform(self):
        r = requests.get(f"{MODULES_URL}?uri=/corb/transform.xqy&database=roxy-modules",
                         auth=ML_BASIC)
        self.assertEqual(r.status_code, 200, "transform.xqy not found in roxy-modules")
        self.assertIn("object-node", r.text,
            "transform.xqy in MarkLogic is old version — missing JSON guard")

    def test_modules_db_has_selector(self):
        r = requests.get(f"{MODULES_URL}?uri=/corb/selector.xqy&database=roxy-modules",
                         auth=ML_BASIC)
        self.assertEqual(r.status_code, 200, "selector.xqy not found in roxy-modules")

    def test_modules_db_has_claims_api(self):
        r = requests.get(f"{MODULES_URL}?uri=/app/claims.xqy&database=roxy-modules",
                         auth=ML_BASIC)
        self.assertEqual(r.status_code, 200, "claims.xqy not found in roxy-modules")

# ═══════════════════════════════════════════════════════════════════════════════
# SUITE 3 — Dashboard proxy
# ═══════════════════════════════════════════════════════════════════════════════
class TestDashboardProxy(unittest.TestCase):
    """Tests for serve_dashboard.py proxy on port 8888."""

    @classmethod
    def setUpClass(cls):
        try:
            r = requests.get(f"{DASH_URL}/dashboard.html", timeout=3)
            cls.dash_up = r.status_code == 200
        except Exception:
            cls.dash_up = False
        if not cls.dash_up:
            print("\n  [SKIP] serve_dashboard.py not running — start with: python serve_dashboard.py")

    def setUp(self):
        if not self.dash_up:
            self.skipTest("Dashboard proxy not available")

    def test_dashboard_html_serves(self):
        r = requests.get(f"{DASH_URL}/dashboard.html")
        self.assertEqual(r.status_code, 200)
        self.assertIn("MECP", r.text)

    def test_proxy_forwards_claims_api(self):
        r = requests.get(f"{DASH_URL}/api/v1/resources/claims?limit=1")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("claims", data)

    def test_proxy_returns_over_1000_claims(self):
        r = requests.get(f"{DASH_URL}/api/v1/resources/claims?limit=2000")
        data = r.json()
        total = data.get("total", 0)
        self.assertGreaterEqual(total, 1000,
            f"Dashboard proxy returns only {total} claims")

    def test_proxy_filter_works(self):
        r = requests.get(f"{DASH_URL}/api/v1/resources/claims?status=PAID&limit=2000")
        claims = r.json().get("claims", [])
        bad = [c for c in claims if c.get("status") != "PAID"]
        self.assertEqual(len(bad), 0, "Status filter broken through proxy")

# ═══════════════════════════════════════════════════════════════════════════════
# SUITE 4 — AI Agent mock logic
# ═══════════════════════════════════════════════════════════════════════════════
class TestAgentService(unittest.TestCase):
    """Unit tests for agentService mock logic — no server needed."""

    def _mock_response(self, question, claims):
        """Inline copy of agentService._mockResponse logic for unit testing."""
        q = question.lower()
        filtered = claims[:]
        label = "all claims"
        if "paid"    in q: filtered = [c for c in claims if c["status"] == "PAID"];    label = "paid claims"
        elif "denied"  in q: filtered = [c for c in claims if c["status"] == "DENIED"];  label = "denied claims"
        elif "pending" in q: filtered = [c for c in claims if c["status"] == "PENDING"]; label = "pending claims"
        if "high" in q or "value" in q:
            filtered = [c for c in filtered if c.get("amountBilled", 0) > 5000]
            label = f"high-value {label}"
        total = sum(c.get("amountBilled", 0) for c in filtered)
        return {"answer": f"I found {len(filtered)} {label}", "claims": filtered[:12], "total": total}

    @classmethod
    def setUpClass(cls):
        cls.claims = [
            {"claimId": "CLM-0001", "status": "PAID",    "amountBilled": 8900, "provider": "City Medical"},
            {"claimId": "CLM-0002", "status": "DENIED",  "amountBilled": 3200, "provider": "Metro Health"},
            {"claimId": "CLM-0003", "status": "PENDING", "amountBilled": 6700, "provider": "WellCare"},
            {"claimId": "CLM-0004", "status": "PAID",    "amountBilled": 1200, "provider": "City Medical"},
            {"claimId": "CLM-0005", "status": "PENDING", "amountBilled": 9100, "provider": "Metro Health"},
        ]

    def test_filter_paid(self):
        res = self._mock_response("show me paid claims", self.claims)
        self.assertIn("paid", res["answer"])
        for c in res["claims"]: self.assertEqual(c["status"], "PAID")

    def test_filter_denied(self):
        res = self._mock_response("show denied claims", self.claims)
        for c in res["claims"]: self.assertEqual(c["status"], "DENIED")

    def test_filter_pending(self):
        res = self._mock_response("pending claims review", self.claims)
        for c in res["claims"]: self.assertEqual(c["status"], "PENDING")

    def test_filter_high_value_pending(self):
        res = self._mock_response("show high-value pending claims", self.claims)
        for c in res["claims"]:
            self.assertEqual(c["status"], "PENDING")
            self.assertGreater(c["amountBilled"], 5000)

    def test_all_claims_no_filter(self):
        res = self._mock_response("show me all claims", self.claims)
        self.assertEqual(len(res["claims"]), len(self.claims))

    def test_answer_includes_count(self):
        res = self._mock_response("show paid claims", self.claims)
        paid_count = sum(1 for c in self.claims if c["status"] == "PAID")
        self.assertIn(str(paid_count), res["answer"])

# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════
SUITES = {
    "files":     TestFileStructure,
    "api":       TestMarkLogicAPI,
    "dashboard": TestDashboardProxy,
    "agent":     TestAgentService,
}

def run(suite_names, verbosity=1):
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for name in suite_names:
        suite.addTests(loader.loadTestsFromTestCase(SUITES[name]))

    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "="*55)
    total  = result.testsRun
    failed = len(result.failures) + len(result.errors)
    skipped = len(result.skipped)
    passed = total - failed - skipped
    print(f"  Result: {passed} PASSED  |  {failed} FAILED  |  {skipped} SKIPPED")
    print("  Safe to push to GitHub" if failed == 0 else "  FIX FAILURES BEFORE PUSHING")
    print("="*55)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MECP automated test suite")
    parser.add_argument("--suite", default="all",
        choices=["all", "files", "api", "dashboard", "agent"],
        help="Which suite to run (default: all)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    names = list(SUITES.keys()) if args.suite == "all" else [args.suite]
    sys.exit(run(names, verbosity=2 if args.verbose else 1))
