xquery version "1.0-ml";

(:
  claims.xqy final filtered/guarded version
  Fixes:
  1. Reads REST extension parameters from rs:status / rs:limit and plain status / limit.
  2. Uses JSON property queries for JSON claim documents.
  3. Removes "unfiltered" from cts:search so MarkLogic must verify matches.
  4. Adds a final output guard so only matching status records are returned.
  5. Keeps directory scope at /claims/ so XML/triple documents are avoided.
:)

declare variable $_ as item()* external;
declare variable $status as xs:string external := "";
declare variable $id     as xs:string external := "";
declare variable $limit  as xs:string external := "2000";

let $request-status    := xdmp:get-request-field("status", "")
let $request-rs-status := xdmp:get-request-field("rs:status", "")
let $request-id        := xdmp:get-request-field("id", "")
let $request-rs-id     := xdmp:get-request-field("rs:id", "")
let $request-limit     := xdmp:get-request-field("limit", "")
let $request-rs-limit  := xdmp:get-request-field("rs:limit", "")

let $status-final :=
  fn:upper-case(fn:normalize-space(
    if ($status ne "") then $status
    else if ($request-rs-status ne "") then $request-rs-status
    else $request-status
  ))

let $id-final :=
  fn:normalize-space(
    if ($id ne "") then $id
    else if ($request-rs-id ne "") then $request-rs-id
    else $request-id
  )

let $limit-final-raw :=
  if ($limit ne "") then $limit
  else if ($request-rs-limit ne "") then $request-rs-limit
  else if ($request-limit ne "") then $request-limit
  else "2000"

let $limit-final :=
  if ($limit-final-raw castable as xs:integer)
  then xs:integer($limit-final-raw)
  else 2000

let $base-query := cts:directory-query("/claims/", "infinity")

let $query :=
  if ($id-final ne "") then
    cts:and-query((
      $base-query,
      cts:json-property-value-query("claimId", $id-final, "exact")
    ))
  else if ($status-final ne "") then
    cts:and-query((
      $base-query,
      cts:json-property-value-query("status", $status-final, "exact")
    ))
  else
    $base-query

(: Important: do NOT use "unfiltered" here. We want verified matches only. :)
let $results := cts:search(fn:doc(), $query)[1 to $limit-final]

let $claims :=
  for $doc in $results
  let $obj := $doc/object-node()
  let $doc-status := fn:upper-case(fn:normalize-space(fn:string($obj/status)))
  let $doc-id := fn:normalize-space(fn:string($obj/claimId))
  where fn:exists($obj)
    and (if ($status-final ne "") then $doc-status eq $status-final else fn:true())
    and (if ($id-final ne "") then $doc-id eq $id-final else fn:true())
  return $obj

return xdmp:to-json(
  map:new((
    map:entry("debug_status_final", $status-final),
    map:entry("debug_id_final", $id-final),
    map:entry("debug_limit_final", $limit-final),
    map:entry("returned", fn:count($claims)),
    map:entry("claims", json:to-array($claims))
  ))
)
