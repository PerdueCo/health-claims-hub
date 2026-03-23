xquery version "1.0-ml";

declare namespace rest = "http://marklogic.com/appservices/rest";

(: Parameters :)
declare variable $_ as item()* external;
declare variable $status as xs:string external := "";
declare variable $id     as xs:string external := "";

(: -------------------------------------------------------
   No hardcoded limit - always returns ALL matching claims
   scoped to /claims/ directory only so triplestore XML
   and framework modules are never included in results.
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
      cts:element-value-query(xs:QName("status"), $status)
    ))
  else
    $base-query

let $results := xdmp:invoke-function(
  function() {
    cts:search(fn:doc(), $query)
  },
  <options xmlns="xdmp:eval">
    <database>{xdmp:database("roxy-content")}</database>
  </options>
)

let $claims :=
  for $doc in $results
  return $doc/object-node()

let $total := fn:count($claims)

return xdmp:to-json(
  map:new((
    map:entry("total", $total),
    if ($status ne "")  then map:entry("filter", $status)  else (),
    if ($id ne "")      then map:entry("id",     $id)       else (),
    map:entry("claims",
      json:to-array(
        for $c in $claims
        return $c
      )
    )
  ))
)
