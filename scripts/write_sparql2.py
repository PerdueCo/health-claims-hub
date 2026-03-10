q = (
    "PREFIX mecp: <http://mecp/ontology#> "
    "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
    "SELECT ?status (COUNT(?claim) AS ?claimCount) (SUM(xsd:decimal(?amountBilled)) AS ?totalBilled) "
    "WHERE { "
    "GRAPH <http://mecp/claims/graph> { "
    "?claim mecp:hasStatus ?status . "
    "?claim mecp:amountBilled ?amountBilled . "
    "} } GROUP BY ?status ORDER BY ?status"
)

xqy = '''xquery version "1.0-ml";
import module namespace sem = "http://marklogic.com/semantics"
  at "/MarkLogic/semantics.xqy";
let $sparql := "''' + q + '''"
let $results := sem:sparql($sparql)
return (
  "=== Total Billed Amount by Status ===",
  for $r in $results return fn:concat(
    "Status: ", map:get($r,"status"),
    " | Claims: ", map:get($r,"claimCount"),
    " | Total Billed: $", map:get($r,"totalBilled")
  )
)'''

with open('corb/sparql-amount-by-status.xqy', 'w', encoding='utf-8', newline='\n') as f:
    f.write(xqy)
print('done')
