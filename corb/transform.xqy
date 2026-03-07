xquery version "1.0-ml";
declare variable $URI as xs:string external;

(: CORB Transform ? adds processedDate to each claim document :)
(: Idempotent: safe to run multiple times ? only updates if not already set :)
let $doc   := fn:doc($URI)
let $map   := xdmp:from-json($doc)
let $today := fn:format-date(fn:current-date(), "[Y0001]-[M01]-[D01]")
return
  if (map:contains($map, "processedDate")) then
    $URI  (: already processed ? skip :)
  else
    let $updated := xdmp:to-json(
      map:with($map, "processedDate", $today)
    )
    return xdmp:document-insert($URI, $updated)
