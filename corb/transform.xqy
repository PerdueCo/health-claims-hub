xquery version "1.0-ml";

(: CORB Transform - 6-step pipeline
   Only called for /claims/ URIs (selector scopes to /claims/) :)

declare variable $URI as xs:string external;

(: Skip anything that slips through that is not a JSON claim :)
if (fn:not(fn:ends-with($URI, ".json"))) then $URI
else

let $doc  := fn:doc($URI)
let $node := $doc/object-node()

(: Step 1 - validate required fields :)
let $valid := (
  fn:exists($node/claimId) and
  fn:exists($node/status)  and
  fn:exists($node/amountBilled)
)

return
  if (fn:not($valid)) then
    fn:error(xs:QName("INVALID-CLAIM"), fn:concat("Missing required fields: ", $URI))
  else

(: Step 2 - enrich: add processingDate and platformVersion :)
let $enriched := xdmp:from-json(xdmp:to-json(
  map:new((
    xdmp:from-json(xdmp:to-json($node)),
    map:entry("processingDate",   fn:string(fn:current-date())),
    map:entry("platformVersion",  "MECP-1.1")
  ))
))

(: Step 3 - categorize by amountBilled :)
let $priority :=
  if ($node/amountBilled > 5000) then "HIGH"
  else if ($node/amountBilled > 1000) then "MEDIUM"
  else "LOW"

let $categorized := xdmp:from-json(xdmp:to-json(
  map:new((
    $enriched,
    map:entry("priority", $priority)
  ))
))

(: Step 4 - flag high-value claims :)
let $flagged := xdmp:from-json(xdmp:to-json(
  map:new((
    $categorized,
    if ($node/amountBilled > 5000)
    then map:entry("highValueReview", fn:true())
    else ()
  ))
))

(: Step 5 - normalize status to uppercase :)
let $normalized := xdmp:from-json(xdmp:to-json(
  map:new((
    $flagged,
    map:entry("status", fn:upper-case(fn:normalize-space(fn:string($node/status))))
  ))
))

(: Step 6 - mark pipeline complete :)
let $final := xdmp:from-json(xdmp:to-json(
  map:new((
    $normalized,
    map:entry("pipelineComplete", fn:true())
  ))
))

return xdmp:node-replace($node, xdmp:to-json($final)/node())
