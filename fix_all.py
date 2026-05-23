"""
MECP Fix Script - uploads corrected modules directly to MarkLogic
Run from: C:\Users\cash america\documents\projects\health-claims-hub
"""
import requests
from requests.auth import HTTPBasicAuth
import os, sys

ML_HOST  = "localhost"
ML_PORT  = 8041
ML_USER  = "admin"
ML_PASS  = "admin123"
AUTH     = HTTPBasicAuth(ML_USER, ML_PASS)
BASE_URL = f"http://{ML_HOST}:{ML_PORT}/v1/documents"

TRANSFORM_XQY = '''xquery version "1.0-ml";
declare variable $URI as xs:string external;

(: CORB Transform - adds processedDate to each claim document :)
(: Skips non-JSON documents such as triplestore XML :)

let $doc := fn:doc($URI)
return
  if (fn:empty($doc/object-node())) then
    $URI  (: not a JSON object - skip silently :)
  else
    let $map   := xdmp:from-json($doc)
    let $today := fn:format-date(fn:current-date(), "[Y0001]-[M01]-[D01]")
    return
      if (map:contains($map, "processedDate")) then
        $URI  (: already processed - skip :)
      else
        let $updated := xdmp:to-json(
          map:with($map, "processedDate", $today)
        )
        return xdmp:document-insert($URI, $updated)
'''

SELECTOR_XQY = '''xquery version "1.0-ml";
(: CORB Selector - scoped to /claims/ directory only :)
(: Excludes triplestore XML and any other non-claim documents :)
let $uris := cts:uris((), (), cts:directory-query("/claims/", "infinity"))
return (fn:count($uris), $uris)
'''

CLAIMS_XQY = '''xquery version "1.0-ml";

declare namespace rest = "http://marklogic.com/appservices/rest";

declare variable $_ as item()* external;
declare variable $status as xs:string external := "";
declare variable $id     as xs:string external := "";
declare variable $limit  as xs:integer external := 2000;

let $base-query := cts:directory-query("/claims/", "infinity")

let $query :=
  if ($id ne "") then
    cts:and-query((
      $base-query,
      cts:document-query(fn:concat("/claims/", fn:lower-case($id), ".json"))
    ))
  else if ($status ne "") then
    cts:and-query((
      $base-query,
      cts:json-property-value-query("status", $status)
    ))
  else
    $base-query

let $real-total := xdmp:invoke-function(
  function() { cts:estimate($query) },
  <options xmlns="xdmp:eval">
    <database>{xdmp:database("roxy-content")}</database>
  </options>
)

let $results := xdmp:invoke-function(
  function() { cts:search(fn:doc(), $query)[1 to $limit] },
  <options xmlns="xdmp:eval">
    <database>{xdmp:database("roxy-content")}</database>
  </options>
)

let $claims :=
  for $doc in $results
  return $doc/object-node()

return xdmp:to-json(
  map:new((
    map:entry("total", $real-total),
    if ($status ne "") then map:entry("filter", $status) else (),
    if ($id ne "")     then map:entry("id",     $id)     else (),
    map:entry("claims",
      json:to-array(for $c in $claims return $c)
    )
  ))
)
'''

def upload(uri, content, db="roxy-modules"):
    url = f"{BASE_URL}?uri={uri}&database={db}"
    r = requests.put(
        url,
        data=content.encode("utf-8"),
        headers={"Content-Type": "application/xquery"},
        auth=AUTH
    )
    if r.status_code in (200, 201, 204):
        print(f"  OK   {uri}")
    else:
        print(f"  FAIL {uri} -> HTTP {r.status_code}: {r.text[:200]}")

def verify_total():
    url = f"http://{ML_HOST}:8040/v1/resources/claims?limit=2000"
    r = requests.get(url, auth=AUTH)
    if r.status_code == 200:
        data = r.json()
        print(f"\n  API total returned : {data.get('total')}")
        print(f"  Claims in response : {len(data.get('claims', []))}")
        statuses = {}
        for c in data.get("claims", []):
            s = c.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        print(f"  Status breakdown   : {statuses}")
    else:
        print(f"  API test failed: HTTP {r.status_code}")

print("\n" + "="*50)
print("  MECP Module Fix Script")
print("="*50)

print("\nUploading fixed modules to MarkLogic...")
upload("/corb/transform.xqy",  TRANSFORM_XQY)
upload("/corb/selector.xqy",   SELECTOR_XQY)
upload("/app/claims.xqy",      CLAIMS_XQY)

print("\nVerifying API after fix...")
verify_total()

print("\nDone. Now run: python scripts\\run_pipeline.py")
print("="*50)


