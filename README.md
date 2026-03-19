# MarkLogic Enterprise Claims Platform (MECP)

> Enterprise-grade healthcare claims processing platform built on **MarkLogic 11**
> Fully containerized - Deployable in 3 commands - Verifiable in 5 minutes

A production-style platform demonstrating senior MarkLogic developer capabilities
including REST API development, XQuery programming, range indexing, bulk data ingestion,
CORB batch processing, semantic triple storage, SPARQL querying, live dashboard,
and containerized deployment - built to federal consulting delivery standards.

---

## Quick Start

```powershell
# 1 - Clone
git clone https://github.com/PerdueCo/health-claims-hub
cd health-claims-hub

# 2 - Start (first run takes 2-3 minutes)
docker compose up -d

# 3 - Verify (wait 30 seconds after docker compose up)
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

**Expected result:**
```
========================================
Result: 6 PASSED | 0 FAILED
Platform is READY for demonstration
========================================
```

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
| Bulk data load | MLCP - 1000 claims loaded | Complete |
| Batch processing | CORB - 6-step pipeline, 1010 claims | Complete |
| Semantic triples | RDF triple store - 8000 triples | Complete |
| SPARQL queries | Aggregation and filter queries on live data | Complete |
| Live dashboard | HTML dashboard with proxy server | Complete |

---

## System Architecture

![System Architecture](docs/MECP_System_Architecture.png)

---

## Live Dashboard

The MECP dashboard displays live claims data from MarkLogic in your browser.

**Step 1 - Start the platform (if not already running):**
```powershell
docker compose up -d
```

**Step 2 - Start the dashboard server:**
```powershell
python serve_dashboard.py
```

**Step 3 - Open in Chrome:**
```
http://localhost:8888/dashboard.html
```

Leave `serve_dashboard.py` running while using the dashboard. The server acts
as a proxy between the browser and MarkLogic, handling authentication and
eliminating browser CORS restrictions.

**Dashboard features:**
- KPI cards - Total, Paid, Denied, Pending claim counts with animated bars
- Status distribution with live percentage bars
- Financial summary - total billed, allowed, paid, denied/pending exposure
- Top 10 providers by claim volume with status breakdown
- Full claims table with filter buttons (All / Paid / Denied / Pending)
- Auto-refreshes every 30 seconds
- No hardcoded limit - shows all claims regardless of database size

---

## Data Pipeline

![Data Pipeline](docs/MECP_Data_Pipeline.png)

The 6-step CORB pipeline processes every claim document in sequence:

| Step | Transform | What It Does |
|---|---|---|
| 1 | validate-claim | Checks required fields are present |
| 2 | enrich-claim | Adds processingDate and platformVersion |
| 3 | categorize-claim | Assigns priority based on amountBilled |
| 4 | flag-high-value | Flags claims over $5000 for review |
| 5 | normalize-status | Uppercases and trims status field |
| 6 | mark-processed | Adds pipelineComplete: true |

Load bulk claims and run the pipeline:
```powershell
python scripts\generate_claims.py          # default 1000 claims
python scripts\generate_claims.py 5000     # or any count you want
python scripts\run_pipeline.py
```

---

## Semantic Triples and SPARQL

8000 RDF triples are generated from the 1000 bulk claims (8 predicates per claim)
and stored in the named graph http://mecp/claims/graph.

Generate and load triples:
```powershell
python scripts\write_triples.py
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/triples-generate.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

Query total billed by status:
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

Sample result:
```
Status: DENIED  | Claims: 313 | Total Billed: $1,216,306
Status: PAID    | Claims: 503 | Total Billed: $2,079,633
Status: PENDING | Claims: 184 | Total Billed: $760,165
```

See docs/SPARQL_GUIDE.md for full documentation.

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

---

## Port Reference

| Port | Service | Auth | Purpose |
|---|---|---|---|
| 8001 | MarkLogic Admin UI | admin/admin123 | Browser-based administration |
| 8002 | Manage API | Digest | Platform health and management |
| 8000 | App Services | Digest | /v1/eval, /v1/ping, SPARQL |
| 8040 | MECP REST Server | Basic | Claims API endpoints |
| 8041 | XDBC Server | Basic | MLCP bulk ingest port |

---

## Repository Structure

```
health-claims-hub/
+-- README.md                        <- This file
+-- TESTING.md                       <- Six-level verification guide
+-- CORB_GUIDE.md                    <- CORB pipeline documentation
+-- docker-compose.yml               <- One-command platform startup
+-- dashboard.html                   <- Live claims dashboard
+-- serve_dashboard.py               <- Dashboard proxy server
|
+-- docs/
|   +-- MECP_System_Architecture.png <- System architecture diagram
|   +-- MECP_Data_Pipeline.png       <- Data pipeline diagram
|   +-- SPARQL_GUIDE.md              <- SPARQL query documentation
|   +-- RCA_MarkLogic_Upgrade.md     <- Incident root cause analysis
|   +-- HIPAA_COMPLIANCE.md          <- HIPAA compliance documentation
|   +-- MECP_Setup_Guide.pdf         <- Step-by-step setup for new machines
|
+-- claims-roxy/
|   +-- deploy/
|   |   +-- build.properties         <- App server configuration
|   |   +-- local.properties         <- Docker connection settings
|   |   +-- ml-config.xml            <- Databases, forests, range indexes
|   +-- data/claims/                 <- 10 seed JSON claim documents
|   +-- src/app/
|       +-- claims.xqy               <- REST API controller (XQuery)
|       +-- config.xqy               <- App configuration (XQuery)
|
+-- corb/
|   +-- selector.xqy                 <- CORB document selector
|   +-- transform.xqy                <- CORB 6-step pipeline transform
|   +-- corb.properties              <- CORB job configuration
|   +-- triples-generate.xqy         <- RDF triple generator
|   +-- sparql-pending-by-provider.xqy  <- SPARQL query 1
|   +-- sparql-amount-by-status.xqy     <- SPARQL query 2
|
+-- data/
|   +-- bulk-claims/                 <- JSON claims (count depends on generate_claims.py)
|
+-- scripts/
    +-- verify.ps1                   <- Windows verification (6 tests)
    +-- verify.sh                    <- Mac/Linux verification
    +-- generate_claims.py           <- Bulk claims generator (accepts count argument)
    +-- run_pipeline.py              <- CORB pipeline runner
    +-- write_triples.py             <- Triple generator file writer
    +-- run-mlcp.ps1                 <- MLCP bulk load script
```

---

## Prerequisites

| Requirement | Version | Download |
|---|---|---|
| Docker Desktop | 4.x or higher | https://www.docker.com/products/docker-desktop |
| Git | Any recent | https://git-scm.com |
| Python 3 | 3.8 or higher | https://www.python.org/downloads |
| RAM | 8 GB recommended | MarkLogic minimum is 4 GB |

No MarkLogic license required - the Docker image includes a free developer license.

See docs/MECP_Setup_Guide.pdf for full step-by-step setup instructions.

---

## Infrastructure Decisions

**Why is the Docker image digest-pinned?**
Docker tags are mutable. A vendor can silently replace an image behind an existing tag.
The SHA256 digest pin in docker-compose.yml guarantees identical bytes on every machine,
every time - immune to upstream changes.

**Why is the range index in ml-config.xml?**
Admin UI changes live only in the Docker volume. A docker compose down -v destroys them.
Declaring the index in ml-config.xml means Roxy recreates it automatically on every
bootstrap - making the configuration reproducible and source-controlled.

**Why two authentication methods?**
MarkLogic runs independent server types with separate auth configurations. The Manage API
and App Services use digest auth by default. The MECP REST server uses basic auth as
configured in build.properties. Each endpoint must be called with the correct method.

**Why a triple index for claims data?**
Document queries answer "find claims where status = PENDING". Semantic triples answer
"which providers have the most PENDING claims and what is the total dollar exposure?" -
relationship and aggregation queries that span all documents. The SPARQL layer adds
graph query capability on top of the existing document store with no schema changes.

**Why a proxy server for the dashboard?**
Browsers block cross-origin requests (CORS). The Python proxy server sits between the
browser and MarkLogic, forwarding API calls and handling authentication so the browser
never touches MarkLogic directly.

**Why no hardcoded limit on the claims API?**
A hardcoded limit breaks silently when the database grows. The API now returns all
documents in /claims/ regardless of count - 10, 1000, or 10000. The dashboard
always reflects the true state of the database.

---

## HIPAA Compliance

All data in this platform is 100% synthetic. No real patient names, SSNs, member IDs,
or Protected Health Information (PHI) of any kind are stored in this project.

See docs/HIPAA_COMPLIANCE.md for production deployment controls.

---

## Verification

Six levels of verification are documented in TESTING.md:

| Level | What It Proves | How |
|---|---|---|
| 1 - Runtime | Platform is running and responding | powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 |
| 2 - Persistence | Configuration survives a full rebuild | docker compose down -v + rebuild |
| 3 - Portability | Works on any machine from a fresh clone | Follow MECP_Setup_Guide.pdf |
| 4 - Pipeline | MLCP + CORB process all claims correctly | python scripts\run_pipeline.py |
| 5 - Dashboard | Live data loads in browser | python serve_dashboard.py |
| 6 - SPARQL | Triple queries return correct results | curl sparql-amount-by-status.xqy |

---

## Incident Documentation

During development a MarkLogic version upgrade caused three compounding failures.
Full Root Cause Analysis in docs/RCA_MarkLogic_Upgrade.md.

---

## Development Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Docker + Roxy deployment pipeline | Complete |
| Phase 2 | 10 seed claims loaded, range index active | Complete |
| Phase 3 | Verify script - 6 PASSED | Complete |
| Phase 4 | /v1/resources/claims REST endpoint | Complete |
| Phase 5 | Single claim lookup, status filter | Complete |
| Phase 6 | CORB batch pipeline - 6 transforms, 1010 claims | Complete |
| Phase 7 | MLCP bulk load - 1000 claims ingested | Complete |
| Phase 8 | Semantic triples + SPARQL - 8000 triples, 2 queries | Complete |
| Phase 9 | Architecture diagrams + RCA documentation | Complete |
| Phase 10 | Setup guide PDF + HIPAA compliance docs | Complete |
| Phase 11 | README accurate + all phases documented | Complete |
| Phase 12 | Bug fixes - triplestore scope, verify command, claims limit | Complete |
| Phase 13 | Live dashboard + proxy server | Complete |
| Phase 14 | Final polish + v1.1 release tag | In Progress |

---

## Documentation

| Document | Description |
|---|---|
| docs/MECP_Setup_Guide.pdf | Step-by-step setup for a fresh Windows machine |
| docs/HIPAA_COMPLIANCE.md | HIPAA compliance - synthetic data statement and production controls |
| docs/SPARQL_GUIDE.md | SPARQL guide - named graph, ontology, example queries |
| docs/RCA_MarkLogic_Upgrade.md | Root cause analysis - three compounding failures |
| docs/MECP_System_Architecture.png | System architecture diagram |
| docs/MECP_Data_Pipeline.png | Data pipeline diagram |

---

*MarkLogic Enterprise Claims Platform - v1.1*
*Built to enterprise consulting delivery standards*
