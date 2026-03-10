# SPARQL Guide — MECP Semantic Triples

**MarkLogic Enterprise Claims Platform**

MarkLogic is a multi-model database. In addition to storing JSON documents, it has a
built-in RDF triple store that supports SPARQL 1.1 — the W3C standard query language
for linked data. This guide explains how the MECP platform uses semantic triples to
express relationships between healthcare claims and how to query those relationships
using SPARQL.

---

## What Are RDF Triples?

An RDF triple is a statement in the form:

```
Subject  →  Predicate  →  Object
```

For a healthcare claim this looks like:

```
http://mecp/claims/CLM-0011  mecp:hasStatus    "PENDING"
http://mecp/claims/CLM-0011  mecp:hasProvider  "Statesboro Health Clinic"
http://mecp/claims/CLM-0011  mecp:hasMember    "M-10043"
http://mecp/claims/CLM-0011  mecp:hasState     "GA"
http://mecp/claims/CLM-0011  mecp:amountBilled "3437"
```

Each triple is a fact. A collection of triples forms a **knowledge graph** — a web of
relationships that can be traversed and queried in ways that document queries cannot
easily express.

---

## MECP Ontology

All MECP predicates are defined under the namespace `http://mecp/ontology#`:

| Predicate | Description | Example Value |
|---|---|---|
| `mecp:hasStatus` | Claim processing status | `PAID`, `DENIED`, `PENDING` |
| `mecp:hasProvider` | Healthcare provider name | `Statesboro Health Clinic` |
| `mecp:hasMember` | Member identifier | `M-10043` |
| `mecp:hasState` | Facility state | `GA` |
| `mecp:hasCity` | Facility city | `Statesboro` |
| `mecp:amountBilled` | Submitted billed amount | `3437` |
| `mecp:serviceDate` | Date of service | `2025-08-19` |
| `mecp:hasCollection` | MarkLogic collection | `bulk-claims` |
| `rdf:type` | RDF class | `mecp:Claim` |

---

## Named Graph

All MECP triples are stored in a single named graph:

```
http://mecp/claims/graph
```

Using a named graph means the triples are isolated from any other triple data in the
database and can be queried, updated, or dropped as a unit.

---

## Step 1 — Generate and Store Triples

Run the triple generator to build RDF triples from all 1000 bulk claims and store them
in the named graph:

```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/triples-generate.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Expected output:**
```
Triples inserted: 9000 | Graph: http://mecp/claims/graph | Claims processed: 1000
```

Nine triples are generated per claim (rdf:type + 8 predicates) × 1000 claims = 9000 triples.

---

## Step 2 — Verify the Named Graph Exists

Confirm the graph was created and count the triples:

```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=sem:graph-size(sem:iri('http://mecp/claims/graph'))&database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Expected output:**
```
9000
```

---

## SPARQL Query 1 — PENDING Claims by Provider

Returns all PENDING claims with provider, member, amount billed, and city.
Sorted by provider name so related claims are grouped together.

```sparql
PREFIX mecp: <http://mecp/ontology#>

SELECT ?claimId ?provider ?memberId ?amountBilled ?city
WHERE {
  GRAPH <http://mecp/claims/graph> {
    ?claim mecp:hasStatus     "PENDING" .
    ?claim mecp:hasProvider   ?provider .
    ?claim mecp:hasMember     ?memberId .
    ?claim mecp:amountBilled  ?amountBilled .
    ?claim mecp:hasCity       ?city .
  }
  BIND(REPLACE(STR(?claim), "http://mecp/claims/", "") AS ?claimId)
}
ORDER BY ?provider ?claimId
```

**Run via XQuery wrapper:**

```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-pending-by-provider.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample output:**
```
PENDING claims found: 186
Provider: Athens Regional Medical Center | Claim: CLM-0023 | Member: M-10091 | Billed: $2150 | City: Athens
Provider: Athens Regional Medical Center | Claim: CLM-0187 | Member: M-10304 | Billed: $4820 | City: Athens
Provider: Emory University Hospital     | Claim: CLM-0044 | Member: M-10112 | Billed: $6300 | City: Atlanta
...
```

---

## SPARQL Query 2 — Total Billed Amount by Status

Aggregates total billed amount and claim count grouped by status.
Demonstrates SPARQL 1.1 aggregation functions: `GROUP BY`, `COUNT`, `SUM`.

```sparql
PREFIX mecp: <http://mecp/ontology#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

SELECT ?status
       (COUNT(?claim) AS ?claimCount)
       (SUM(xsd:decimal(?amountBilled)) AS ?totalBilled)
WHERE {
  GRAPH <http://mecp/claims/graph> {
    ?claim mecp:hasStatus    ?status .
    ?claim mecp:amountBilled ?amountBilled .
  }
}
GROUP BY ?status
ORDER BY ?status
```

**Run via XQuery wrapper:**

```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample output (counts and amounts vary — data is randomized):**
```
=== Total Billed Amount by Status ===
Status: DENIED  | Claims: 316 | Total Billed: $1,842,300
Status: PAID    | Claims: 508 | Total Billed: $2,961,540
Status: PENDING | Claims: 186 | Total Billed: $1,083,720
```

---

## How Triples Are Generated

The XQuery module `corb/triples-generate.xqy` iterates over every document in the
`bulk-claims` collection and emits 9 triples per document:

```xquery
declare namespace sem = "http://marklogic.com/semantics";

let $subject := sem:iri(fn:concat("http://mecp/claims/", $c/claimId))
return (
  sem:triple($subject, $RDF-TYPE,       $MECP-CLAIM),
  sem:triple($subject, $HAS-STATUS,     fn:string($c/status)),
  sem:triple($subject, $HAS-PROVIDER,   fn:string($c/provider)),
  sem:triple($subject, $HAS-MEMBER,     fn:string($c/memberId)),
  sem:triple($subject, $HAS-STATE,      fn:string($c/facility/state)),
  sem:triple($subject, $HAS-CITY,       fn:string($c/facility/city)),
  sem:triple($subject, $AMOUNT-BILLED,  fn:string($c/amountBilled)),
  sem:triple($subject, $SERVICE-DATE,   fn:string($c/serviceDate)),
  sem:triple($subject, $HAS-COLLECTION, "bulk-claims")
)
```

All triples are inserted as a single transaction using `sem:graph-insert()`.

---

## Why Semantic Triples?

| Capability | Document Query | Semantic Triple Query |
|---|---|---|
| Find a claim by ID | `cts:doc("/claims/CLM-0011.json")` | `?claim mecp:hasStatus "PAID"` |
| Count by status | `cts:values()` with range index | `COUNT(?claim) GROUP BY ?status` |
| Traverse relationships | Not supported natively | `?claim mecp:hasProvider ?p . ?p mecp:hasState "GA"` |
| Aggregate financial data | Requires XQuery iteration | `SUM(xsd:decimal(?amountBilled))` |
| Interoperability | Proprietary JSON structure | W3C standard RDF/SPARQL |

Semantic triples are most powerful when relationships span multiple entity types — for
example, linking claims to providers, providers to networks, networks to contracts.
The MECP triple store is the foundation for that kind of graph query.

---

## Dropping and Regenerating Triples

If you need to regenerate the triples (for example after reloading claims):

```powershell
# Drop the named graph
curl.exe --digest -u admin:admin123 `
  --data "xquery=sem:graph-delete(sem:iri('http://mecp/claims/graph'))&database=roxy-content" `
  http://localhost:8000/v1/eval

# Regenerate
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/triples-generate.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

---

## File Reference

| File | Purpose |
|---|---|
| `corb/triples-generate.xqy` | Generates and stores 9000 RDF triples from bulk-claims |
| `corb/sparql-pending-by-provider.xqy` | SPARQL query: PENDING claims sorted by provider |
| `corb/sparql-amount-by-status.xqy` | SPARQL query: total billed amount aggregated by status |
| `docs/SPARQL_GUIDE.md` | This file |

---

## Further Reading

- [MarkLogic Semantics Developer Guide](https://docs.marklogic.com/guide/semantics)
- [SPARQL 1.1 W3C Specification](https://www.w3.org/TR/sparql11-query/)
- [MarkLogic sem:sparql() function](https://docs.marklogic.com/sem:sparql)
