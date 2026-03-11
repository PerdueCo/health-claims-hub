# MarkLogic Enterprise Claims Platform (MECP)

> Enterprise-grade healthcare claims processing platform built on **MarkLogic 11**
> Fully containerized · Deployable in 3 commands · Verifiable in 5 minutes

A production-style platform demonstrating senior MarkLogic developer capabilities
including REST API development, XQuery programming, range indexing, bulk data ingestion,
batch processing, semantic triple storage, SPARQL querying, and containerized
deployment — built to federal consulting delivery standards.

---

## Quick Start

```powershell
# 1 — Clone
git clone https://github.com/PerdueCo/health-claims-hub
cd health-claims-hub

# 2 — Start (first run takes 2-3 minutes)
docker compose up -d
docker logs -f health-claims-hub-roxy-1

# 3 — Verify (run after you see "Roxy deploy COMPLETE")
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
./scripts/verify.sh           # Mac / Linux
```

**Expected result:**
```
========================================
Result: 6 PASSED | 0 FAILED
Platform is READY for demonstration
========================================
```

---

## System Architecture

![MECP System Architecture](docs/MECP_System_Architecture.png)

```
+--------------------------------------------------+
|                  CLIENT LAYER                    |
|         curl · Postman · verify.ps1              |
+------------------+-------------------------------+
                   |
       +-----------+-----------+
       v                       v
+-------------+         +-------------+
|  Port 8040  |         |  Port 8000  |
|  REST API   |         |  App Svcs   |
|  basic auth |         | digest auth |
+------+------+         +------+------+
       |                       |
       +-----------+-----------+
                   v
+--------------------------------------------------+
|            MarkLogic 11  (Port 8002)             |
|                                                  |
|  Database: roxy-content                          |
|  +-- 1010 JSON healthcare claim documents        |
|  +-- Element range index on status field         |
|  +-- bulk-claims collection (1000 documents)     |
|  +-- 8000 RDF triples in named graph             |
|                                                  |
|  Database: roxy-modules                          |
|  +-- 81 XQuery modules                           |
+--------------------------------------------------+
                   |
                   | XDBC :8041
                   v
+--------------------------------------------------+
|         Roxy Container (Docker)                  |
|   Ruby + Java 17 + MLCP 12 + deploy.sh           |
+--------------------------------------------------+
```

---

## Bulk Data Load (1000 Claims)

After the platform is running, load the full claim dataset:

```powershell
# Generate 1000 randomized claim documents
python scripts/generate_claims.py

# Run the controlled 6-step pipeline
python scripts/run_pipeline.py
```

**Expected pipeline output:**
```
STEP 1 - Inspecting database state
STEP 2 - Identifying missing documents
STEP 3 - Loading missing documents via MLCP (Docker)
STEP 4 - Validating loaded documents        10/10 passed
STEP 5 - Running CORB (stamp processedDate) 1010/1010 complete
STEP 6 - Final report
  Total documents              : 1010
  Bulk-claims collection       : 1000
  Documents with processedDate : 1010
  Status distribution          : PAID / DENIED / PENDING (randomized)
```

## Data Pipeline

![MECP Data Pipeline](docs/MECP_Data_Pipeline.png)

---

## Semantic Triples and SPARQL

8000 RDF triples are generated from the 1000 bulk claims (8 predicates per claim)
and stored in the named graph `http://mecp/claims/graph`.

**Generate and load triples:**
```powershell
python scripts/write_triples.py
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/triples-generate.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Query — total billed amount by status:**
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample SPARQL result:**
```
Status: DENIED  | Claims: 313 | Total Billed: $1,216,306
Status: PAID    | Claims: 503 | Total Billed: $2,079,633
Status: PENDING | Claims: 184 | Total Billed: $760,165
```

**Query — PENDING claims by provider:**
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-pending-by-provider.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

See [docs/SPARQL_GUIDE.md](docs/SPARQL_GUIDE.md) for full documentation.

---

## What This Platform Demonstrates

| Capability | Technology | Status |
|---|---|---|
| Containerized deployment | Docker Compose + Roxy | Complete |
| Automated bootstrap | Roxy ml deploy pipeline | Complete |
| REST API layer | XQuery on MarkLogic App Server | Complete |
| Claims collection endpoint | GET /v1/resources/claims | Complete |
| Status filter | ?status=PAID, DENIED, PENDING | Complete |
| Single claim lookup | ?id=CLM-0001 | Complete |
| Search and indexing | cts:values, element range index | Complete |
| Bulk data load | MLCP via Docker — 1000 claims | Complete |
| Batch processing | CORB — processedDate stamping | Complete |
| Controlled pipeline | 6-step idempotent run_pipeline.py | Complete |
| Semantic triples | RDF triple store — 8000 triples | Complete |
| SPARQL queries | Aggregation + filter queries on live data | Complete |

---

## API Reference

### GET all claims
```powershell
curl.exe -u admin:admin123 http://localhost:8040/v1/resources/claims
```

### Filter by status
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=PAID"
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=DENIED"
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=PENDING"
```

### Single claim lookup
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?id=CLM-0001"
```

### Document count (ad-hoc XQuery)
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=cts:estimate(cts:true-query())&database=roxy-content" `
  http://localhost:8000/v1/eval
```

### Status distribution
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=for $v in cts:values(cts:json-property-reference('status')) return concat($v,': ',cts:frequency($v))&database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample response:**
```json
{
  "total": 1,
  "filter": "CLM-0011",
  "claims": [{
    "claimId": "CLM-0011",
    "memberId": "M-10043",
    "provider": "Statesboro Health Clinic",
    "serviceDate": "2025-08-19",
    "status": "PENDING",
    "amountBilled": 3437,
    "facility": { "state": "GA", "city": "Statesboro" },
    "processedDate": "2026-03-09"
  }]
}
```

---

## Port Reference

| Port | Service | Auth | Purpose |
|---|---|---|---|
| 8001 | MarkLogic Admin UI | admin/admin123 | Browser-based administration |
| 8002 | Manage API | Digest | Platform health and management |
| 8000 | App Services | Digest | /v1/eval, /v1/ping, SPARQL |
| 8040 | MECP REST Server | Basic | Claims API endpoints |
| 8041 | XDBC Server | Digest | MLCP bulk load, CORB batch |

---

## Repository Structure

```
health-claims-hub/
+-- README.md                         <- This file
+-- TESTING.md                        <- Three-level verification guide
+-- CORB_GUIDE.md                     <- CORB architecture and usage
+-- docker-compose.yml                <- One-command platform startup
|
+-- roxy/
|   +-- Dockerfile                    <- Ruby + Java 17 + MLCP 12
|   +-- deploy.sh                     <- Bootstrap and deploy automation
|   +-- mlcp-load.sh                  <- MLCP import script (baked into image)
|   +-- mlcp/lib/                     <- MLCP 12 jar files
|
+-- claims-roxy/
|   +-- deploy/
|   |   +-- build.properties          <- App server configuration
|   |   +-- local.properties          <- Docker connection settings
|   |   +-- ml-config.xml             <- Databases, forests, range indexes
|   +-- data/claims/                  <- 10 seed JSON claim documents
|   +-- src/app/
|       +-- claims.xqy                <- REST API controller (XQuery)
|
+-- corb/
|   +-- selector.xqy                  <- CORB document selector
|   +-- transform.xqy                 <- CORB processedDate transform
|   +-- corb.properties               <- CORB job configuration
|   +-- triples-generate.xqy          <- RDF triple generator (8000 triples)
|   +-- sparql-pending-by-provider.xqy <- SPARQL query 1
|   +-- sparql-amount-by-status.xqy   <- SPARQL query 2
|
+-- data/
|   +-- bulk-claims/                  <- 1000 generated JSON claim documents
|
+-- docs/
|   +-- MECP_System_Architecture.png  <- System architecture diagram
|   +-- MECP_Data_Pipeline.png        <- Data pipeline diagram
|   +-- RCA_MarkLogic_Upgrade.md      <- Incident root cause analysis
|   +-- SPARQL_GUIDE.md               <- SPARQL query documentation
|   +-- HIPAA_COMPLIANCE.md           <- HIPAA compliance documentation
|   +-- MECP_Setup_Guide.pdf          <- Step-by-step setup for new machines
|
+-- scripts/
    +-- generate_claims.py            <- Generates 1000 randomized bulk claims
    +-- run_pipeline.py               <- Controlled 6-step data pipeline
    +-- write_triples.py              <- Writes triples-generate.xqy
    +-- write_sparql1.py              <- Writes sparql-pending-by-provider.xqy
    +-- write_sparql2.py              <- Writes sparql-amount-by-status.xqy
    +-- delete_bad_uris.py            <- Database cleanup utility
    +-- tag_collections.py            <- Collection tagging utility
    +-- run-mlcp.ps1                  <- MLCP bulk load script
    +-- verify.ps1                    <- Windows verification (6 tests)
    +-- verify.sh                     <- Mac/Linux verification (6 tests)
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Desktop | 4.x or higher | https://www.docker.com/products/docker-desktop |
| Python | 3.8 or higher | For pipeline and generator scripts |
| Git | Any recent | https://git-scm.com |
| Java | 11 or higher | For CORB batch processing |
| RAM | 8 GB recommended | MarkLogic minimum is 4 GB |

No MarkLogic license required — the Docker image includes a free developer license.

See [docs/MECP_Setup_Guide.pdf](docs/MECP_Setup_Guide.pdf) for full step-by-step
setup instructions for a brand-new Windows machine.

---

## Infrastructure Decisions

**Why is the Docker image digest-pinned?**
Docker tags are mutable. A vendor can silently replace an image behind an existing tag.
The SHA256 digest pin in `docker-compose.yml` guarantees identical bytes on every machine,
every time — immune to upstream changes.

**Why is the range index in ml-config.xml?**
Admin UI changes live only in the Docker volume. A `docker compose down -v` destroys them.
Declaring the index in `ml-config.xml` means Roxy recreates it automatically on every
bootstrap — making the configuration reproducible and source-controlled.

**Why does MLCP run inside Docker?**
The bulk load script `mlcp-load.sh` is baked into the Roxy Docker image at build time.
This eliminates local Java and MLCP installation requirements and makes the pipeline
portable across any machine that has Docker — no path or environment configuration needed.

**Why two authentication methods?**
MarkLogic runs independent server types with separate auth configurations. The Manage API
and App Services use digest auth by default. The MECP REST server uses basic auth as
configured in `build.properties`. Each endpoint must be called with the correct method.

**Why is the pipeline idempotent?**
`run_pipeline.py` performs a URI-level diff before loading. If all 1000 documents are
already in the database, Step 3 is skipped entirely. CORB's selector module only returns
documents without a processedDate, so re-running never duplicates work.

**Why a triple index for claims data?**
Document queries answer "find claims where status = PENDING". Semantic triples answer
"which providers have the most PENDING claims and what is the total dollar exposure?" —
relationship and aggregation queries that span all 1000 documents. The SPARQL layer adds
graph query capability on top of the existing document store with no schema changes.

---

## HIPAA Compliance

All data in this platform is 100% synthetic. No real patient names, SSNs, member IDs,
or Protected Health Information (PHI) of any kind are stored in this project. All
claim documents are generated by `scripts/generate_claims.py`.

See [docs/HIPAA_COMPLIANCE.md](docs/HIPAA_COMPLIANCE.md) for production deployment
controls including encryption at rest, role-based access, audit logging, and
HIPAA-eligible hosting requirements.

---

## Verification

Three levels of verification are documented in `TESTING.md`:

| Level | What It Proves | How |
|---|---|---|
| Level 1 — Runtime | Platform is running and responding | `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` |
| Level 2 — Persistence | Configuration survives a full rebuild | `docker compose down -v` + rebuild |
| Level 3 — Portability | Works on any machine from a fresh clone | Follow MECP_Setup_Guide.pdf |

---

## Incident Documentation

During development a MarkLogic version upgrade caused three compounding failures:
Docker tag drift, authentication mismatch, and a missing element range index.
A full Root Cause Analysis with timeline, prevention controls, and lessons learned
is documented in [docs/RCA_MarkLogic_Upgrade.md](docs/RCA_MarkLogic_Upgrade.md).

---

## Development Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Docker + Roxy deployment pipeline | Complete |
| Phase 2 | 10 seed claims loaded, range index active | Complete |
| Phase 3 | Verify script — 6 PASSED | Complete |
| Phase 4 | /v1/resources/claims REST endpoint | Complete |
| Phase 5 | Single claim lookup — ?id=CLM-0001 | Complete |
| Phase 6 | CORB batch processing — processedDate | Complete |
| Phase 7 | MLCP bulk load — 1000 claims via Docker | Complete |
| Phase 8 | Controlled 6-step pipeline | Complete |
| Phase 9 | Architecture diagrams | Complete |
| Phase 10 | Semantic triples + SPARQL — 8000 triples, 2 queries | Complete |
| Phase 11 | Setup guide PDF + HIPAA compliance docs | Complete |
| Phase 12 | Fresh clone end-to-end test | Planned |
| Phase 13 | HTML dashboard | Planned |
| Phase 14 | Final polish and v1.1 tag | Planned |

---

## Supporting Documentation

| Document | Description |
|---|---|
| [docs/MECP_Setup_Guide.pdf](docs/MECP_Setup_Guide.pdf) | Step-by-step setup for a fresh Windows machine |
| [docs/HIPAA_COMPLIANCE.md](docs/HIPAA_COMPLIANCE.md) | HIPAA compliance — synthetic data statement and production controls |
| [docs/SPARQL_GUIDE.md](docs/SPARQL_GUIDE.md) | SPARQL guide — named graph, ontology, example queries |
| [docs/RCA_MarkLogic_Upgrade.md](docs/RCA_MarkLogic_Upgrade.md) | Root cause analysis — three compounding failures |
| [docs/MECP_System_Architecture.png](docs/MECP_System_Architecture.png) | System architecture diagram |
| [docs/MECP_Data_Pipeline.png](docs/MECP_Data_Pipeline.png) | Data pipeline diagram |

---

*MarkLogic Enterprise Claims Platform — v1.1*
*Built to enterprise consulting delivery standards*
