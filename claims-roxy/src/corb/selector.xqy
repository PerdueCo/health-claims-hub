xquery version "1.0-ml";
(: CORB Selector ? returns total count first, then all claim document URIs :)
(: CORB requires count as first item in the sequence :)
let $uris := cts:uris((), (), cts:true-query())
return (fn:count($uris), $uris)
