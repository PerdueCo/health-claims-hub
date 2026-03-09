import os
import sys
import subprocess
import requests
from requests.auth import HTTPDigestAuth

ML_HOST      = "localhost"
ML_REST_PORT = 8000
ML_XCC_PORT  = 8041
ML_USER      = "admin"
ML_PASS      = "admin123"
ML_DATABASE  = "roxy-content"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BULK_DIR     = os.path.join(PROJECT_ROOT, "data", "bulk-claims")

REQUIRED_FIELDS = [
    "claimId", "memberId", "provider", "serviceDate",
    "submittedDate", "status", "amountBilled", "facility"
]

SEED_URIS = set("/claims/clm-{:04d}.json".format(i) for i in range(1, 11))

def sep(title):
    print()
    print("=" * 60)
    print("  " + title)
    print("=" * 60)

def xquery(q):
    r = requests.post(
        "http://{}:{}/v1/eval".format(ML_HOST, ML_REST_PORT),
        data={"xquery": q, "database": ML_DATABASE},
        auth=HTTPDigestAuth(ML_USER, ML_PASS)
    )
    if r.status_code != 200:
        raise RuntimeError("XQuery failed ({}): {}".format(r.status_code, r.text[:300]))
    return r.text

def parse_ints(text):
    out = []
    for line in text.splitlines():
        try:
            out.append(int(line.strip()))
        except Exception:
            pass
    return out

def parse_strings(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("--") and not s.startswith("Content") and not s.startswith("X-"):
            out.append(s)
    return out

def count_collection(name):
    raw = xquery("fn:count(fn:collection('{}'))".format(name))
    vals = parse_ints(raw)
    return vals[0] if vals else 0

def tag_bulk_claims():
    raw  = xquery("cts:uris()")
    uris = [u for u in parse_strings(raw) if u not in SEED_URIS]
    if not uris:
        return 0
    uri_list = ",".join('"{}"'.format(u) for u in uris)
    xq = 'xquery version "1.0-ml"; let $uris := (' + uri_list + ') for $u in $uris return xdmp:document-add-collections($u, "bulk-claims")'
    r = requests.post(
        "http://{}:{}/v1/eval".format(ML_HOST, ML_REST_PORT),
        data={"xquery": xq, "database": ML_DATABASE},
        auth=HTTPDigestAuth(ML_USER, ML_PASS)
    )
    if r.status_code != 200:
        raise RuntimeError("Tagging failed: {}".format(r.text[:300]))
    return len(uris)

def step1():
    sep("STEP 1 - Inspecting database state")
    total = parse_ints(xquery("cts:estimate(cts:true-query())"))[0] if True else 0
    try:
        total = parse_ints(xquery("cts:estimate(cts:true-query())"))[0]
    except Exception:
        total = 0
    bulk = count_collection("bulk-claims")
    seed = total - bulk
    print("  Seed documents (Roxy loaded) : {}".format(seed))
    print("  Bulk documents (MLCP loaded) : {}".format(bulk))
    print("  Total documents              : {}".format(total))
    return total, bulk, seed

def step2():
    sep("STEP 2 - Identifying missing documents")
    if not os.path.exists(BULK_DIR):
        print("  ERROR: {} not found".format(BULK_DIR))
        print("  Run: python scripts/generate_claims.py")
        sys.exit(1)
    on_disk = set(
        "/claims/{}".format(f)
        for f in os.listdir(BULK_DIR)
        if f.endswith(".json")
    )
    print("  Files on disk                : {}".format(len(on_disk)))
    raw   = xquery("for $d in fn:collection('bulk-claims') return fn:document-uri($d)")
    in_db = set(parse_strings(raw))
    print("  URIs already in database     : {}".format(len(in_db)))
    missing = sorted(on_disk - in_db)
    print("  Missing from database        : {}".format(len(missing)))
    return missing

def step3(missing):
    sep("STEP 3 - Loading missing documents via MLCP (Docker)")
    if not missing:
        print("  All documents already loaded - skipping MLCP")
        return
    print("  Documents to load            : {}".format(len(missing)))
    print("  Running MLCP inside Docker...")
    print("  Script baked into image at /mlcp-load.sh")
    print()
    result = subprocess.run([
        "docker", "compose", "run", "--rm",
        "--volume", BULK_DIR + ":/bulk",
        "roxy", "sh", "/mlcp-load.sh"
    ], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("  ERROR: MLCP exited with code {}".format(result.returncode))
        sys.exit(1)
    print()
    print("  Tagging loaded documents with bulk-claims collection...")
    tagged = tag_bulk_claims()
    print("  Tagged                       : {}".format(tagged))
    print("  Verified collection count    : {}".format(count_collection("bulk-claims")))

def step1():
    sep("STEP 1 - Inspecting database state")
    total = parse_ints(xquery("cts:estimate(cts:true-query())"))[0] if True else 0
    try:
        total = parse_ints(xquery("cts:estimate(cts:true-query())"))[0]
    except Exception:
        total = 0
    bulk = count_collection("bulk-claims")
    seed = total - bulk
    print("  Seed documents (Roxy loaded) : {}".format(seed))
    print("  Bulk documents (MLCP loaded) : {}".format(bulk))
    print("  Total documents              : {}".format(total))
    return total, bulk, seed

def step2():
    sep("STEP 2 - Identifying missing documents")
    if not os.path.exists(BULK_DIR):
        print("  ERROR: {} not found".format(BULK_DIR))
        print("  Run: python scripts/generate_claims.py")
        sys.exit(1)
    on_disk = set(
        "/claims/{}".format(f)
        for f in os.listdir(BULK_DIR)
        if f.endswith(".json")
    )
    print("  Files on disk                : {}".format(len(on_disk)))
    raw   = xquery("for $d in fn:collection('bulk-claims') return fn:document-uri($d)")
    in_db = set(parse_strings(raw))
    print("  URIs already in database     : {}".format(len(in_db)))
    missing = sorted(on_disk - in_db)
    print("  Missing from database        : {}".format(len(missing)))
    return missing

def step3(missing):
    sep("STEP 3 - Loading missing documents via MLCP (Docker)")
    if not missing:
        print("  All documents already loaded - skipping MLCP")
        return
    print("  Documents to load            : {}".format(len(missing)))
    print("  Running MLCP inside Docker...")
    print("  Script baked into image at /mlcp-load.sh")
    print()
    result = subprocess.run([
        "docker", "compose", "run", "--rm",
        "--volume", BULK_DIR + ":/bulk",
        "roxy", "sh", "/mlcp-load.sh"
    ], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("  ERROR: MLCP exited with code {}".format(result.returncode))
        sys.exit(1)
    print()
    print("  Tagging loaded documents with bulk-claims collection...")
    tagged = tag_bulk_claims()
    print("  Tagged                       : {}".format(tagged))
    print("  Verified collection count    : {}".format(count_collection("bulk-claims")))

def step4():
    sep("STEP 4 - Validating loaded documents")
    sample = parse_strings(
        xquery("for $d in subsequence(fn:collection('bulk-claims'),1,10) return fn:document-uri($d)")
    )
    if not sample:
        print("  ERROR: No bulk-claims documents found after load")
        sys.exit(1)
    print("  Validating sample of {} documents...".format(len(sample)))
    print()
    failed = 0
    passed = 0
    for uri in sample:
        doc_raw = xquery("fn:doc('{}')".format(uri))
        missing_flds = [f for f in REQUIRED_FIELDS if '"{}"'.format(f) not in doc_raw]
        if missing_flds:
            failed += 1
            print("  FAIL  {}  missing: {}".format(uri, missing_flds))
        else:
            passed += 1
            print("  PASS  {}".format(uri))
    print()
    print("  Result                       : {}/{} passed".format(passed, len(sample)))
    if failed:
        print("  ERROR: Validation failed.")
        sys.exit(1)
    print("  All sampled documents are structurally valid")

def step5():
    sep("STEP 5 - Running CORB (stamp processedDate)")
    corb = os.path.join(PROJECT_ROOT, "claims-roxy", "deploy", "lib", "java", "marklogic-corb-2.3.2.jar")
    xcc  = os.path.join(PROJECT_ROOT, "claims-roxy", "deploy", "lib", "java", "marklogic-xcc-9.0.1.jar")
    print("  Stamping processedDate on unprocessed documents...")
    print("  Documents already processed will be skipped (idempotent)")
    print()
    r = subprocess.run([
        "java",
        "-cp", "{};{}".format(corb, xcc),
        "-DXCC-CONNECTION-URI=xcc://{}:{}@{}:{}/{}".format(
            ML_USER, ML_PASS, ML_HOST, ML_XCC_PORT, ML_DATABASE),
        "-DURIS-MODULE=selector.xqy",
        "-DPROCESS-MODULE=transform.xqy",
        "-DTHREAD-COUNT=2",
        "-DMODULE-ROOT=/corb/",
        "-DMODULES-DATABASE=roxy-modules",
        "com.marklogic.developer.corb.Manager"
    ])
    if r.returncode != 0:
        print("  ERROR: CORB exited with code {}".format(r.returncode))
        sys.exit(1)

def step6():
    sep("STEP 6 - Final report")
    total     = parse_ints(xquery("cts:estimate(cts:true-query())"))
    bulk      = count_collection("bulk-claims")
    processed = parse_ints(xquery(
        "cts:estimate(cts:json-property-scope-query('processedDate',cts:true-query()))"
    ))
    statuses = [
        s for s in parse_strings(xquery(
            "for $v in cts:values(cts:json-property-reference('status')) return concat($v,': ',cts:frequency($v))"
        )) if ":" in s
    ]
    print("  Total documents              : {}".format(total[0] if total else 0))
    print("  Bulk-claims collection       : {}".format(bulk))
    print("  Documents with processedDate : {}".format(processed[0] if processed else 0))
    print()
    print("  Status distribution:")
    for s in statuses:
        print("    {}".format(s))
    print()
    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)

def main():
    print()
    print("=" * 60)
    print("  MECP Controlled Data Pipeline")
    print("  MarkLogic Enterprise Claims Platform")
    print("=" * 60)
    step1()
    missing = step2()
    step3(missing)
    step4()
    step5()
    step6()

if __name__ == "__main__":
    main()
