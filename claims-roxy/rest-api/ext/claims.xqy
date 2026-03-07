xquery version "1.0-ml";

module namespace claims = "http://marklogic.com/rest-api/resource/claims";

(:
  MECP Claims REST Extension
  Endpoint: GET /v1/resources/claims
  Auth:     Basic (port 8040)

  Parameters:
    rs:status  — optional filter: PAID | DENIED | PENDING
    rs:limit   — optional max results (default 100)

  Examples:
    GET /v1/resources/claims
    GET /v1/resources/claims?rs:status=PENDING
    GET /v1/resources/claims?rs:status=PAID&rs:limit=10
:)

declare %roxy:params("status=xs:string,limit=xs:int")
function claims:get(
  $context as map:map,
  $params  as map:map
) as document-node()
{
  (: --- parameters ------------------------------------------------- :)
  let $status := map:get($params, "status")
  let $limit  := let $l := map:get($params, "limit")
                 return if ($l) then $l else 100

  (: --- build search query ----------------------------------------- :)
  let $query :=
    if ($status and $status != "")
    then cts:element-value-query(xs:QName("status"), $status)
    else cts:true-query()

  (: --- execute search against roxy-content ------------------------- :)
  let $results :=
    xdmp:invoke-function(
      function() {
        subsequence(
          cts:search(fn:collection(), $query),
          1,
          $limit
        )
      },
      <options xmlns="xdmp:eval">
        <database>{xdmp:database("roxy-content")}</database>
      </options>
    )

  (: --- build response --------------------------------------------- :)
  let $claims :=
    for $doc in $results
    return $doc/node()

  return document {
    object-node {
      "total"   : fn:count($claims),
      "filter"  : if ($status) then $status else "none",
      "claims"  : array-node { $claims }
    }
  }
};
