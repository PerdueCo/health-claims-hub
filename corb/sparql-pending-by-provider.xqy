xquery version "1.0-ml";
import module namespace sem = "http://marklogic.com/semantics"
  at "/MarkLogic/semantics.xqy";
let $sparql := "PREFIX mecp: <http://mecp/ontology#> SELECT ?claimId ?provider ?memberId ?amountBilled ?city WHERE { GRAPH <http://mecp/claims/graph> { ?claim mecp:hasStatus 'PENDING' . ?claim mecp:hasProvider ?provider . ?claim mecp:hasMember ?memberId . ?claim mecp:amountBilled ?amountBilled . ?claim mecp:hasCity ?city . } BIND(REPLACE(STR(?claim), 'http://mecp/claims/', '') AS ?claimId) } ORDER BY ?provider ?claimId"
let $results := sem:sparql($sparql)
return (
  fn:concat("PENDING claims found: ", fn:string(fn:count($results))),
  for $r in $results return fn:concat(
    "Provider: ", map:get($r,"provider"),
    " | Claim: ", map:get($r,"claimId"),
    " | Member: ", map:get($r,"memberId"),
    " | City: ", map:get($r,"city")
  )
)