xquery version "1.0-ml";

import module namespace sem = "http://marklogic.com/semantics"
  at "/MarkLogic/semantics.xqy";

declare variable $GRAPH         := sem:iri("http://mecp/claims/graph");
declare variable $BASE          := "http://mecp/claims/";
declare variable $HAS-STATUS    := sem:iri("http://mecp/ontology#hasStatus");
declare variable $HAS-PROVIDER  := sem:iri("http://mecp/ontology#hasProvider");
declare variable $HAS-MEMBER    := sem:iri("http://mecp/ontology#hasMember");
declare variable $HAS-STATE     := sem:iri("http://mecp/ontology#hasState");
declare variable $HAS-CITY      := sem:iri("http://mecp/ontology#hasCity");
declare variable $AMOUNT-BILLED := sem:iri("http://mecp/ontology#amountBilled");
declare variable $SERVICE-DATE  := sem:iri("http://mecp/ontology#serviceDate");
declare variable $RDF-TYPE      := sem:iri("http://www.w3.org/1999/02/22-rdf-syntax-ns#type");
declare variable $MECP-CLAIM    := sem:iri("http://mecp/ontology#Claim");

let $triples :=
  for $doc in fn:collection("bulk-claims")
  let $c       := $doc/node()
  let $id      := fn:string($c/claimId)
  let $subject := sem:iri(fn:concat($BASE, $id))
  return (
    sem:triple($subject, $RDF-TYPE,      $MECP-CLAIM),
    sem:triple($subject, $HAS-STATUS,    fn:string($c/status)),
    sem:triple($subject, $HAS-PROVIDER,  fn:string($c/provider)),
    sem:triple($subject, $HAS-MEMBER,    fn:string($c/memberId)),
    sem:triple($subject, $HAS-STATE,     fn:string($c/facility/state)),
    sem:triple($subject, $HAS-CITY,      fn:string($c/facility/city)),
    sem:triple($subject, $AMOUNT-BILLED, fn:string($c/amountBilled)),
    sem:triple($subject, $SERVICE-DATE,  fn:string($c/serviceDate))
  )

let $_ := sem:graph-insert($GRAPH, $triples)

return fn:count($triples)