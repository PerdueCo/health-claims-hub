import requests
from requests.auth import HTTPDigestAuth

auth = HTTPDigestAuth("admin", "admin123")
base = "http://localhost:8000/v1/eval"

SEED = set("/claims/clm-{:04d}.json".format(i) for i in range(1, 11))

# Get all URIs
r = requests.post(base, data={
    "xquery": "cts:uris()",
    "database": "roxy-content"
}, auth=auth)
print("URI fetch status:", r.status_code)

uris = [
    line.strip() for line in r.text.splitlines()
    if line.strip()
    and not line.strip().startswith("--")
    and not line.strip().startswith("Content")
    and not line.strip().startswith("X-")
]

bulk_uris = [u for u in uris if u not in SEED]
print("Bulk URIs found:", len(bulk_uris))

# Build one single XQuery with all URIs hardcoded
uri_list = ",\n".join('"{}"'.format(u) for u in bulk_uris)
xq = 'xquery version "1.0-ml";\nlet $uris := (' + uri_list + ')\nfor $u in $uris\nreturn xdmp:document-add-collections($u, "bulk-claims")'

r2 = requests.post(base, data={
    "xquery": xq,
    "database": "roxy-content"
}, auth=auth)
print("Tag status:", r2.status_code)
if r2.status_code != 200:
    print(r2.text[:500])

# Verify
r3 = requests.post(base, data={
    "xquery": 'fn:count(fn:collection("bulk-claims"))',
    "database": "roxy-content"
}, auth=auth)
print("Collection count:", r3.text.strip())
