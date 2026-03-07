xquery version "1.0-ml";

declare option xdmp:mapping "false";

let $_ := xdmp:set-response-content-type("application/json")
let $status := xdmp:get-request-field("status", "")
let $id     := xdmp:get-request-field("id", "")
let $limit  := xs:integer(xdmp:get-request-field("limit", "100"))

let $response :=
  xdmp:invoke-function(
    function() {
      if ($id != "") then
        let $docs := cts:search(
          fn:collection(),
          cts:json-property-value-query("claimId", $id)
        )
        return
          if (fn:exists($docs)) then
            object-node {
              "total"  : 1,
              "filter" : $id,
              "claims" : array-node { $docs/node() }
            }
          else
            object-node {
              "total"   : 0,
              "filter"  : $id,
              "claims"  : array-node {},
              "message" : fn:concat("No claim found with ID: ", $id)
            }
      else
        let $query :=
          if ($status != "")
          then cts:json-property-value-query("status", $status)
          else cts:true-query()
        let $results := subsequence(
          cts:search(fn:collection(), $query),
          1,
          $limit
        )
        let $claims :=
          for $doc in $results
          return $doc/node()
        return object-node {
          "total"  : fn:count($claims),
          "filter" : if ($status != "") then $status else "none",
          "claims" : array-node { $claims }
        }
    },
    <options xmlns="xdmp:eval">
      <database>{xdmp:database("roxy-content")}</database>
    </options>
  )

return xdmp:to-json($response)
