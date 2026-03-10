# Root Cause Analysis & Prevention Report

**MarkLogic Enterprise Claims Platform — Infrastructure Incident**

| Field | Detail |
|---|---|
| Incident ID | MECP-INC-2026-001 |
| Date Opened | March 6, 2026 |
| Date Resolved | March 6, 2026 (same day) |
| Severity | High — blocked all verification testing |
| Status | RESOLVED |
| Project | MarkLogic Enterprise Claims Platform (MECP) |
| Repository | health-claims-hub |

---

## 1. Executive Summary

During deployment of the MarkLogic Enterprise Claims Platform, a version upgrade from
MarkLogic 11.2 to 11.3.3 caused a cascade of three distinct failures that reduced
verification test results from 7 PASSED to 1 PASSED. All three issues were diagnosed
and resolved within a single working session. This document records each failure, its
root cause, the corrective action taken, and the permanent prevention controls now in place.

| Issue | Root Cause Category | Resolution Time | Status |
|---|---|---|---|
| Docker image tag invalid | External dependency drift | < 1 hour | RESOLVED |
| Authentication method mismatch | Port/auth configuration | < 2 hours | RESOLVED |
| Missing element range index | Database config not persisted | < 1 hour | RESOLVED |

---

## 2. Environment

| Component | Before | After |
|---|---|---|
| MarkLogic Version | 11.2.0 | 11.3.3 |
| Docker Image Tag | progressofficial/marklogic-db:11.2.0-ubi9 | progressofficial/marklogic-db:11.3.3-ubi-2.2.2 |
| Image Pinning | Tag only (mutable) | Tag + SHA256 digest (immutable) |
| REST App Server Auth | Basic | Basic |
| App Services Auth | Digest | Digest |
| status Range Index | Not in ml-config.xml | Declared in ml-config.xml |

---

## 3. Incident Timeline

| Time | Event |
|---|---|
| T+0:00 | `docker compose up -d` fails — image `progressofficial/marklogic-db:11.2.0-ubi9` not found |
| T+0:30 | Docker Hub audit identifies correct tag: `11.3.3-ubi-2.2.2`. docker-compose.yml updated. |
| T+1:00 | Container starts healthy. verify.ps1 shows 1 PASSED / 5 FAILED (all 401 Unauthorized) |
| T+1:30 | Root cause identified: verify.ps1 sending `--digest` to port 8040 which requires basic auth |
| T+2:00 | verify.ps1 rewritten with correct auth per port. Result: 5 PASSED / 1 FAILED |
| T+2:30 | Remaining failure: HTTP 500 `XDMP-ELEMRIDXNOTFOUND` on status frequency query |
| T+2:45 | `xdmp:database()` confirms `/v1/eval` on port 8000 targets Documents DB, not roxy-content |
| T+3:00 | status range index added via Admin UI on roxy-content database |
| T+3:15 | eval query updated with `&database=roxy-content` parameter |
| T+3:30 | verify.ps1 result: **6 PASSED \| 0 FAILED — Platform is READY for demonstration** |
| T+3:45 | Prevention controls applied: digest pinned, ml-config.xml updated, committed to git |

---

## 4. Issue 1 — Docker Image Tag Invalid

### 4.1 Symptom

- `docker compose up -d` fails with: `pull access denied, repository does not exist`
- Error: `progressofficial/marklogic-db:11.2.0-ubi9 — manifest unknown`

### 4.2 Root Cause

Progress Software changed the Docker image tag naming convention between MarkLogic 11.2
and 11.3. The `-ubi9` OS suffix was dropped and the tag format changed to
`{ML version}-ubi-{docker-image-version}`. The old tag was removed from Docker Hub when
11.3.3 was published, leaving docker-compose.yml pointing to a non-existent image.

Additionally, Docker Hub tags are mutable — a publisher can point an existing tag name
to a different image at any time. Relying on a tag alone provides no guarantee of
reproducibility.

### 4.3 Corrective Action

- Audited Docker Hub for the latest valid tag: `progressofficial/marklogic-db:11.3.3-ubi-2.2.2`
- Updated `docker-compose.yml` image field to the new tag
- Pinned the image to its immutable SHA256 digest to prevent future drift

### 4.4 Prevention Control

`docker-compose.yml` is now pinned to both tag and digest:

```yaml
image: progressofficial/marklogic-db:11.3.3-ubi-2.2.2@sha256:27fafe66b799c58a5f2e5589307f3571e6a0ea2c24a09be09c3c0e78b7e9e935
```

A digest-pinned image will always pull the exact same bytes regardless of what Progress
Software does to the tag. If an upgrade is needed, it requires a deliberate, reviewed
change to `docker-compose.yml` — it cannot happen silently.

---

## 5. Issue 2 — Authentication Method Mismatch

### 5.1 Symptom

- `verify.ps1` returns HTTP 401 Unauthorized on all REST endpoints (ports 8040 and 8000)
- Manual `curl.exe` without `--digest` flag succeeds on port 8040
- Port 8002 (Manage API) passes correctly

### 5.2 Root Cause

MarkLogic exposes three server types, each with independent authentication configuration.
The verify script incorrectly used `--digest` (HTTP Digest Authentication) for all endpoints.

| Port | Server Type | Auth Method | Configured By |
|---|---|---|---|
| 8002 | Manage API | Digest | MarkLogic default |
| 8000 | App Services | Digest | MarkLogic default |
| 8040 | Roxy App Server | Basic | claims-roxy/deploy/build.properties |

The Roxy `build.properties` file explicitly sets `authentication-method=basic` for the
app server on port 8040. Sending `--digest` to a basic-auth server causes the digest
challenge/response handshake to fail with 401.

### 5.3 Corrective Action

- Rewrote `verify.ps1` with the correct auth method per endpoint
- Port 8002 and 8000 calls use `--digest`
- Port 8040 calls omit `--digest` (basic auth)
- Added port/auth legend to the verify.ps1 output header for operator clarity

### 5.4 Prevention Control

The auth method for each port is now documented in three places: the `verify.ps1`
output header, inline comments in `verify.ps1`, and this RCA. Any future modification
to `build.properties` that changes `authentication-method` must be accompanied by a
corresponding update to `verify.ps1`.

---

## 6. Issue 3 — Missing Element Range Index

### 6.1 Symptom

- `POST /v1/eval` with `cts:values()` query returns HTTP 500
- Error: `XDMP-ELEMRIDXNOTFOUND: cts:element-reference(fn:QName("","status"))`
- Full error: `No element range index for status collation=http://marklogic.com/collation/`

### 6.2 Root Cause

Two compounding problems caused this failure:

1. The `status` element range index was not defined in `ml-config.xml`. It had been
   added manually via the Admin UI in a previous session but never committed to the Roxy
   configuration file. When `docker compose down -v` destroyed the volume, the index was lost.

2. The `/v1/eval` endpoint on port 8000 (App Services) defaults to the Documents database,
   not `roxy-content` where claim data lives. The `cts:values()` query was running against
   the wrong database even after the index was restored.

### 6.3 Corrective Action

- Added the `status` range element index declaration to `claims-roxy/deploy/ml-config.xml`
- Roxy now creates the index automatically on every bootstrap — no manual Admin UI step required
- Updated the `/v1/eval` POST body in `verify.ps1` to include `&database=roxy-content`
- Verified via `xdmp:database-name(xdmp:database())` that the correct database is now targeted

### 6.4 Prevention Control

The range index is now declared in source control and will never be lost to volume destruction:

```xml
<range-element-index>
  <scalar-type>string</scalar-type>
  <namespace-uri/>
  <localname>status</localname>
  <collation>http://marklogic.com/collation/</collation>
  <range-value-positions>false</range-value-positions>
</range-element-index>
```

Any developer who clones the repository and runs `docker compose up -d` will have the
range index created automatically.

---

## 7. Verification Results — Before & After

| Test | Port | Before | After |
|---|---|---|---|
| GET /manage/v2 returns status | 8002 | PASS | PASS |
| GET /v1/ping returns OK | 8000 | FAIL (401) | PASS |
| GET /v1/resources returns a response | 8040 | FAIL (401) | PASS |
| GET /v1/resources/claims returns results | 8040 | FAIL (401) | PASS |
| POST /v1/eval - cts:estimate | 8000 | FAIL (401) | PASS |
| POST /v1/eval - status frequency | 8000 | FAIL (500) | PASS |

**Final Result: 6 PASSED | 0 FAILED — Platform is READY for demonstration**

---

## 8. Prevention Controls Summary

| Control | File | Protects Against |
|---|---|---|
| SHA256 digest pin | docker-compose.yml | Silent image tag mutation by vendor |
| Range index in ml-config.xml | claims-roxy/deploy/ml-config.xml | Index loss on `docker compose down -v` |
| Per-port auth in verify.ps1 | scripts/verify.ps1 | Auth mismatch across server types |
| `&database=` in eval queries | scripts/verify.ps1 | Wrong database targeted by /v1/eval |
| All controls in source control | git commit + push | Configuration drift between environments |

---

## 9. Lessons Learned

- **Never rely on mutable Docker image tags** for reproducible demos. Always pin to a SHA256 digest.
- **MarkLogic Admin UI changes are ephemeral.** Every configuration change must be reflected in `ml-config.xml` before it can be considered permanent.
- **MarkLogic runs multiple server types** on different ports with independent authentication. Verification scripts must account for this explicitly.
- **`/v1/eval` targets the Documents database by default.** Queries against application data must specify `&database=` explicitly.
- **Changed error codes indicate progress** — a shift from 401 to 500 means a different layer is being reached. Systematic, one-fix-at-a-time diagnosis is faster than guessing.

---

## 10. Sign-Off

| Item | Detail |
|---|---|
| Incident resolved | Yes — March 6, 2026 |
| Verification passing | 6 PASSED \| 0 FAILED |
| Controls committed | Yes — docker-compose.yml, ml-config.xml, verify.ps1 |
| Pushed to GitHub | Yes |
| Demo readiness | READY — reproducible from git clone |
