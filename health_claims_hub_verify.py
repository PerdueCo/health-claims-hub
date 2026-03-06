"""health_claims_hub_verify.py

Repeatable verification script for your MarkLogic Docker demo.
- Labels every step
- Uses Digest auth (required by MarkLogic)
- Calls MarkLogic /v1/eval with JavaScript safely

Prereqs:
  - Python 3.9+
  - pip install requests
  - Docker Desktop running
  - Run this from your project folder (where docker-compose.yml is)

Usage:
  python .\health_claims_hub_verify.py
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import requests
from requests.auth import HTTPDigestAuth


@dataclass
class Config:
    project_dir: str
    docker_compose_cmd: str
    ml_container_name: str
    ml_host_inside_compose: str
    admin_user: str
    admin_pass: str
    local_admin_port: int
    local_manage_port: int
    local_app_port: int


def banner(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_cmd(cmd: str, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        text=True,
        capture_output=True
    )


def print_cmd_result(label: str, proc: subprocess.CompletedProcess) -> None:
    print(f"\n--- {label} ---")
    print(f"Exit code: {proc.returncode}")
    if proc.stdout.strip():
        print("STDOUT:")
        print(proc.stdout.rstrip())
    if proc.stderr.strip():
        print("STDERR:")
        print(proc.stderr.rstrip())


def http_head(url: str, auth: Optional[HTTPDigestAuth] = None, timeout: int = 10) -> int:
    r = requests.head(url, auth=auth, timeout=timeout, allow_redirects=False)
    return r.status_code


def http_get(url: str, auth: Optional[HTTPDigestAuth] = None, timeout: int = 10) -> requests.Response:
    return requests.get(url, auth=auth, timeout=timeout, allow_redirects=False)


def eval_js_v1(host: str, port: int, js: str, user: str, password: str, timeout: int = 20) -> str:
    url = f"http://{host}:{port}/v1/eval"
    auth = HTTPDigestAuth(user, password)
    r = requests.post(url, auth=auth, data={"javascript": js}, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"/v1/eval failed: HTTP {r.status_code}\n{r.text[:1200]}")
    return r.text.strip()


def safe_preview(text: str, max_chars: int = 800) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "\n... (truncated) ..."


def guess_compose_command() -> str:
    p = run_cmd("docker compose version")
    if p.returncode == 0:
        return "docker compose"
    p2 = run_cmd("docker-compose version")
    if p2.returncode == 0:
        return "docker-compose"
    return "docker compose"


def step_1_docker_ps(cfg: Config) -> None:
    banner("STEP 1 — Docker Compose Status (docker compose ps)")
    proc = run_cmd(f"{cfg.docker_compose_cmd} ps", cwd=cfg.project_dir)
    print_cmd_result("docker compose ps", proc)


def step_2_docker_logs(cfg: Config) -> None:
    banner("STEP 2 — MarkLogic Container Logs (last 50 lines)")
    proc = run_cmd(f"docker logs {cfg.ml_container_name} --tail 50", cwd=cfg.project_dir)
    print_cmd_result("docker logs --tail 50", proc)


def step_3_admin_head_local(cfg: Config) -> None:
    banner("STEP 3 — Local Admin Port Reachability (expect 401 Digest challenge)")
    url = f"http://localhost:{cfg.local_admin_port}/"
    try:
        code = http_head(url, timeout=10)
        print(f"HEAD {url} -> HTTP {code}")
        print("Expected: 401 is OK (server is alive; Digest challenge).")
    except Exception as e:
        print(f"FAILED to reach {url}: {e}")


def step_4_manage_api_digest(cfg: Config) -> None:
    banner("STEP 4 — Manage API Digest Auth Check (expect 200)")
    url = f"http://{cfg.ml_host_inside_compose}:{cfg.local_manage_port}/manage/v2"
    try:
        auth = HTTPDigestAuth(cfg.admin_user, cfg.admin_pass)
        r = http_get(url, auth=auth, timeout=15)
        print(f"GET {url} -> HTTP {r.status_code}")
        if r.status_code == 200:
            print("OK: Manage API reachable with Digest auth.")
        else:
            print("Unexpected status. Body preview:")
            print(safe_preview(r.text))
    except Exception as e:
        print(f"Manage API check failed: {e}")


def step_5_list_databases(cfg: Config) -> None:
    banner("STEP 5 — List Databases (Manage API)")
    url = f"http://{cfg.ml_host_inside_compose}:{cfg.local_manage_port}/manage/v2/databases"
    try:
        auth = HTTPDigestAuth(cfg.admin_user, cfg.admin_pass)
        r = http_get(url, auth=auth, timeout=20)
        print(f"GET {url} -> HTTP {r.status_code}")
        if r.status_code == 200:
            print("OK: Databases list retrieved. Preview (first ~20 lines):")
            print("\n".join(r.text.splitlines()[:20]))
        else:
            print("Failed to list databases. Body preview:")
            print(safe_preview(r.text))
    except Exception as e:
        print(f"Databases list failed: {e}")


def step_6_eval_queries(cfg: Config) -> None:
    banner("STEP 6 — /v1/eval Proof Queries (counts + first 10 IDs)")

    js_total = 'cts.estimate(cts.jsonPropertyExistsQuery("claimId"))'
    js_unique = 'fn.count(fn.distinctValues(cts.jsonPropertyReference("claimId")))'
    js_first10 = (
        'fn.stringJoin('
        'fn.subsequence(fn.distinctValues(cts.jsonPropertyReference("claimId")), 1, 10),'
        '"\\n")'
    )

    try:
        total = eval_js_v1(cfg.ml_host_inside_compose, cfg.local_app_port, js_total, cfg.admin_user, cfg.admin_pass)
        unique = eval_js_v1(cfg.ml_host_inside_compose, cfg.local_app_port, js_unique, cfg.admin_user, cfg.admin_pass)
        first10 = eval_js_v1(cfg.ml_host_inside_compose, cfg.local_app_port, js_first10, cfg.admin_user, cfg.admin_pass)

        print("Query A — TOTAL docs with claimId:")
        print(f"  {total}")

        print("\nQuery B — UNIQUE claimIds:")
        print(f"  {unique}")

        try:
            t = int(total.strip())
            u = int(unique.strip())
            if t > u:
                print(f"\nNOTE: TOTAL ({t}) > UNIQUE ({u}) → duplicates likely (loaded more than once).")
            else:
                print(f"\nNOTE: TOTAL ({t}) == UNIQUE ({u}) → no duplicates detected.")
        except Exception:
            print("\nNOTE: Could not parse totals as integers, but outputs are still valid proof.")

        print("\nQuery C — first 10 unique claimIds:")
        print(first10)

    except Exception as e:
        print("ERROR: /v1/eval failed.")
        print(str(e))


def step_7_show_claim_samples(cfg: Config) -> None:
    banner("STEP 7 — Print 5 sample claim docs (claimId + memberId + status + uri)")

    js_samples = (
        'cts.search(cts.jsonPropertyExistsQuery("claimId")).toArray().slice(0,5).map(function(d){'
        'var o=d.toObject();'
        'return {uri: fn.documentUri(d), claimId:o.claimId, memberId:o.memberId, status:o.status, amountPaid:o.amountPaid};'
        '})'
    )

    try:
        out = eval_js_v1(cfg.ml_host_inside_compose, cfg.local_app_port, js_samples, cfg.admin_user, cfg.admin_pass)
        print("Sample output (JSON array):")
        print(out)
    except Exception as e:
        print("ERROR: sample print failed.")
        print(str(e))


def main():
    parser = argparse.ArgumentParser(description="Verify MarkLogic + claims demo is healthy and repeatable.")
    parser.add_argument("--project-dir", default=os.getcwd(), help="Folder that contains docker-compose.yml")
    parser.add_argument("--compose-cmd", default=None, help='Override: "docker compose" or "docker-compose"')
    parser.add_argument("--ml-container", default="ml", help="MarkLogic container name (default: ml)")
    parser.add_argument("--ml-host", default="ml", help="Hostname reachable from roxy container (default: ml)")
    parser.add_argument("--user", default="admin", help="MarkLogic admin username")
    parser.add_argument("--password", default="admin123", help="MarkLogic admin password")
    parser.add_argument("--admin-port", type=int, default=8001, help="Local admin port (default: 8001)")
    parser.add_argument("--manage-port", type=int, default=8002, help="Local manage port (default: 8002)")
    parser.add_argument("--app-port", type=int, default=8000, help="Local app services port (default: 8000)")
    args = parser.parse_args()

    compose_cmd = args.compose_cmd or guess_compose_command()

    cfg = Config(
        project_dir=os.path.abspath(args.project_dir),
        docker_compose_cmd=compose_cmd,
        ml_container_name=args.ml_container,
        ml_host_inside_compose=args.ml_host,
        admin_user=args.user,
        admin_pass=args.password,
        local_admin_port=args.admin_port,
        local_manage_port=args.manage_port,
        local_app_port=args.app_port,
    )

    banner("Health Claims Hub — MarkLogic Demo Verification")
    print(f"Project dir: {cfg.project_dir}")
    print(f"Compose cmd: {cfg.docker_compose_cmd}")
    print(f"ML container: {cfg.ml_container_name}")
    print(f"ML host (inside compose): {cfg.ml_host_inside_compose}")
    print(f"Ports: app={cfg.local_app_port}, admin={cfg.local_admin_port}, manage={cfg.local_manage_port}")
    print("Note: 401 on admin port is expected (Digest challenge). Manage API should be 200 with Digest.\n")

    step_1_docker_ps(cfg)
    step_2_docker_logs(cfg)
    step_3_admin_head_local(cfg)
    step_4_manage_api_digest(cfg)
    step_5_list_databases(cfg)
    step_6_eval_queries(cfg)
    step_7_show_claim_samples(cfg)

    banner("DONE")
    print("Tip: If TOTAL > UNIQUE, you likely loaded duplicates — add a clean-delete step before reload for demos.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print("\nFATAL ERROR:")
        print(e)
        sys.exit(2)
