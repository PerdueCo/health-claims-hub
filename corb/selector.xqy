xquery version "1.0-ml";
(: CORB Selector - scoped to /claims/ directory only :)
(: Excludes triplestore XML and any other non-claim documents :)
let $uris := cts:uris((), (), cts:directory-query("/claims/", "infinity"))
return (fn:count($uris), $uris)
