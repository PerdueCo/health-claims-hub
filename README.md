# MarkLogic Enterprise Claims Platform (MECP)

> Enterprise-grade healthcare claims processing platform built on **MarkLogic 11**  
> Fully containerized · Deployable in 3 commands · Verifiable in 5 minutes

A production-style platform demonstrating senior MarkLogic developer capabilities
including REST API development, XQuery programming, range indexing, batch processing,
and containerized deployment — built to federal consulting delivery standards.

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
.\scripts\verify.ps1          # Windows
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

## What This Platform Demonstrates

| Capability | Technology | Status |
|---|---|---|
| Containerized deployment | Docker Compose + Roxy | ✅ Complete |
| Automated bootstrap | Roxy ml deploy pipeline | ✅ Complete |
| REST API layer | XQuery on MarkLogic App Server | ✅ Complete |
| Claims collection endpoint | GET /v1/resources/claims | ✅ Complete |
| Status filter | ?status=PAID, DENIED, PENDING | ✅ Complete |
| Single claim lookup | ?id=CLM-0001 | ✅ Complete |
| Search and indexing | cts:values, element range index | ✅ Complete |
| Batch processing | CORB — Content Reprocessing in Bulk | 🔄 In Progress |
| Bulk data load | MLCP — MarkLogic Content Pump | 📋 Planned |
| Semantic triples | RDF triple store, SPARQL | 📋 Planned |

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                 CLIENT LAYER                    │
│        curl · Postman · verify.ps1              │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌─────────────┐         ┌─────────────┐
│  Port 8040  │         │  Port 8000  │
│  REST API   │         │  App Svcs   │
│  basic auth │         │ digest auth │
└──────┬──────┘         └──────┬──────┘
       │                       │
       └──────────┬────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│            MarkLogic 11  (Port 8002)            │
│                                                 │
│  Database: roxy-content                         │
│  ├── 10 JSON healthcare claim documents         │
│  └── Element range index on status field        │
│                                                 │
│  Database: roxy-modules                         │
│  └── 79 XQuery modules                          │
└─────────────────────────────────────────────────┘
```

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

### Ad-hoc XQuery — document count
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=cts:estimate(cts:true-query())&database=roxy-content" `
  http://localhost:8000/v1/eval
```

### Ad-hoc XQuery — status frequency
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=for+`$v+in+cts:values(cts:element-reference(xs:QName('status')))+return+concat(`$v,': ',cts:frequency(`$v))&database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample response:**
```json
{
  "total": 5,
  "filter": "PAID",
  "claims": [
    {
      "claimId": "CLM-0001",
      "memberId": "M-10001",
      "provider": "Peachtree Clinic",
      "serviceDate": "2025-12-18",
      "status": "PAID",
      "amountBilled": 420,
      "amountAllowed": 310,
      "amountPaid": 295,
      "diagnosisCodes": ["J06.9"],
      "procedureCodes": ["99213"],
      "facility": { "state": "GA", "city": "Atlanta" }
    }
  ]
}
```

---

## Port Reference

| Port | Service | Auth | Purpose |
|---|---|---|---|
| 8001 | MarkLogic Admin UI | admin/admin123 | Browser-based administration |
| 8002 | Manage API | Digest | Platform health and management |
| 8000 | App Services | Digest | /v1/eval, /v1/ping |
| 8040 | MECP REST Server | Basic | Claims API endpoints |

---

## Repository Structure

```
health-claims-hub/
├── README.md                    ← This file
├── TESTING.md                   ← Three-level verification guide
├── docker-compose.yml           ← One-command platform startup
│
├── roxy/
│   ├── Dockerfile               ← Ruby + Roxy deployment container
│   └── deploy.sh                ← Bootstrap and deploy automation
│
├── claims-roxy/
│   ├── deploy/
│   │   ├── build.properties     ← App server configuration
│   │   ├── local.properties     ← Docker connection settings
│   │   └── ml-config.xml        ← Databases, forests, range indexes
│   ├── data/claims/             ← 10 sample JSON claim documents
│   └── src/app/
│       └── claims.xqy           ← REST API controller (XQuery)
│
└── scripts/
    ├── verify.ps1               ← Windows verification (6 tests)
    └── verify.sh                ← Mac/Linux verification (6 tests)
```

---

## Prerequisites

| Requirement | Version | Download |
|---|---|---|
| Docker Desktop | 4.x or higher | https://www.docker.com/products/docker-desktop |
| Git | Any recent | https://git-scm.com |
| RAM | 8 GB recommended | MarkLogic minimum is 4 GB |

No MarkLogic license required — the Docker image includes a free developer license.

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

**Why two authentication methods?**
MarkLogic runs independent server types with separate auth configurations. The Manage API
and App Services use digest auth by default. The Roxy app server was configured with basic
auth in `build.properties`. Each endpoint must be called with the correct method.

---

## Verification

Three levels of verification are documented in `TESTING.md`:

| Level | What It Proves | How |
|---|---|---|
| Level 1 — Runtime | Platform is running and responding | `.\scripts\verify.ps1` |
| Level 2 — Persistence | Configuration survives a full rebuild | `docker compose down -v` + rebuild |
| Level 3 — Portability | Works on any machine from a fresh clone | Day 13 fresh clone test |

---

## Incident Documentation

During development a MarkLogic version upgrade caused three compounding failures:
Docker tag drift, authentication mismatch, and a missing element range index.
A full Root Cause Analysis with timeline, prevention controls, and lessons learned
is available in `docs/MECP_RCA_Prevention_Report.docx`.

---

## Development Roadmap

| Phase | Description | Status |
|---|---|---|
| ✅ Phase 1 | Docker + Roxy deployment pipeline | Complete |
| ✅ Phase 2 | 10 sample claims loaded, range index active | Complete |
| ✅ Phase 3 | Verify script — 6 PASSED | Complete |
| ✅ Phase 4 | /v1/resources/claims REST endpoint | Complete |
| ✅ Phase 5 | Single claim lookup — ?id=CLM-0001 | Complete |
| 🔄 Phase 6 | CORB batch processing | In Progress |
| 📋 Phase 7 | MLCP bulk load — 1000 claims | Planned |
| 📋 Phase 8 | Semantic triples + SPARQL | Planned |

Full task board: [GitHub Projects](https://github.com/PerdueCo/health-claims-hub/projects)

---

## Important Links

| Resource | URL |
|---|---|
| GitHub Repository | https://github.com/PerdueCo/health-claims-hub |
| Release v1.0-demo | https://github.com/PerdueCo/health-claims-hub/releases/tag/v1.0-demo |
| Project Board | https://github.com/PerdueCo/health-claims-hub/projects |
| MarkLogic Documentation | https://docs.marklogic.com |
| Roxy Framework | https://github.com/marklogic-community/roxy |

---

*MarkLogic Enterprise Claims Platform — v1.0-demo*  
*Built to enterprise consulting delivery standards*
