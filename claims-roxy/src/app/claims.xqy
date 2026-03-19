xquery version "1.0-ml";

import module namespace req = "http://marklogic.com/roxy/request"
  at "/roxy/lib/request.xqy";

declare namespace rest = "http://marklogic.com/appservices/rest";

(: -------------------------------------------------------
   Read request parameters through Roxy request library
------------------------------------------------------- :)
let $status := fn:string((req:get("status"), "")[1])
let $id     := fn:string((req:get("id"), "")[1])
let $limit  :=
  let $raw := fn:string((req:get("limit"), "100")[1])
  return
    if ($raw castable as xs:integer) then xs:integer($raw)
    else 100

(: -------------------------------------------------------
   Build the query - always scoped to /claims/ directory
   so triplestore XML docs are never included in results
------------------------------------------------------- :)
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

let $all-results := xdmp:invoke-function(
  function() {
    cts:search(fn:doc(), $query)
  },
  <options xmlns="xdmp:eval">
    <database>{xdmp:database("roxy-content")}</database>
  </options>
)

let $total := fn:count($all-results)
let $results := $all-results[1 to $limit]

let $claims :=
  for $doc in $results
  return $doc/object-node()

return xdmp:to-json(
  map:new((
    map:entry("total", $total),
    map:entry("returned", fn:count($claims)),
    if ($status ne "") then map:entry("filter", $status) else (),
    if ($id ne "") then map:entry("id", $id) else (),
    map:entry("claims",
      json:to-array(
        for $c in $claims
        return $c
      )
    )
  ))
)
