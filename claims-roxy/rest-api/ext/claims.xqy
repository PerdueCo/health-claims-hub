xquery version "1.0-ml";

module namespace claims = "http://marklogic.com/rest-api/resource/claims";

declare
%roxy:params("limit=xs:int")
function claims:get(
  $context as map:map,
  $params as map:map
) as document-node() {

  let $limit := xs:int(map:get($params,"limit"))

  let $uris :=
    subsequence(
      cts:uris((),(),cts:true-query()),
      1,
      if ($limit) then $limit else 5
    )

  let $docs :=
    for $u in $uris
    return fn:doc($u)/node()

  return
    document {
      object-node {
        "db": xdmp:database-name(xdmp:database()),
        "count": fn:count($docs),
        "uris": array-node { $uris },
        "results": array-node { $docs }
      }
    }
};