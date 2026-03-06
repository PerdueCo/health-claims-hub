content = File.read('deploy/lib/xquery/setup.xqy')

old_func = 'declare function setup:at-least-version($target)
{
  let $current := xdmp:version()
  let $current-formatted :=
    fn:concat(
      fn:format-number(xs:int(fn:replace($current, "^(\\d+)\\..*$", "$1")), "000"), (: major :)
      fn:format-number(xs:int(fn:replace($current, "^\\d+\\.(\\d+).*$", "$1")), "000"), (: minor :)
      fn:format-number(xs:int(fn:replace($current, "^\\d+\\.\\d+\\-(\\d+).*$", "$1")), "000"), (: x.x-X :)
      if (fn:matches($current, "^\\d+\\.\\d+\\-\\d+\\.\\d+$")) then
        fn:format-number(xs:int(fn:replace($current, "^\\d+\\.\\d+\\-\\d+\\.(\\d+)$", "$1")), "000") (: x.x-x.X :)
      else "000"
    )
  let $target-formatted :=
    fn:concat(
      fn:format-number(xs:int(fn:replace($target, "^(\\d+)\\..*$", "$1")), "000"), (: major :)
      fn:format-number(xs:int(fn:replace($target, "^\\d+\\.(\\d+).*$", "$1")), "000"), (: minor :)
      fn:format-number(xs:int(fn:replace($target, "^\\d+\\.\\d+\\-(\\d+).*$", "$1")), "000"), (: x.x-X :)
      if (fn:matches($target, "^\\d+\\.\\d+\\-\\d+\\.\\d+$")) then
        fn:format-number(xs:int(fn:replace($target, "^\\d+\\.\\d+\\-\\d+\\.(\\d+)$", "$1")), "000") (: x.x-x.X :)
      else "000"
    )
  return fn:compare($current-formatted, $target-formatted) >= 0
};'

new_func = 'declare function setup:at-least-version($target)
{
  (: Updated to handle ML11 version format X.X.X as well as old format X.X-X :)
  let $current := xdmp:version()
  let $parse-version := function($v as xs:string) as xs:string {
    let $major := fn:format-number(xs:int(fn:replace($v, "^(\\d+)\\..*$", "$1")), "000")
    let $minor := fn:format-number(xs:int(fn:replace($v, "^\\d+\\.(\\d+).*$", "$1")), "000")
    let $patch :=
      if (fn:matches($v, "^\\d+\\.\\d+\\.\\d+")) then
        fn:format-number(xs:int(fn:replace($v, "^\\d+\\.\\d+\\.(\\d+).*$", "$1")), "000")
      else if (fn:matches($v, "^\\d+\\.\\d+-\\d+")) then
        fn:format-number(xs:int(fn:replace($v, "^\\d+\\.\\d+-(\\d+).*$", "$1")), "000")
      else "000"
    let $build :=
      if (fn:matches($v, "^\\d+\\.\\d+-\\d+\\.\\d+$")) then
        fn:format-number(xs:int(fn:replace($v, "^\\d+\\.\\d+-\\d+\\.(\\d+)$", "$1")), "000")
      else "000"
    return fn:concat($major, $minor, $patch, $build)
  }
  return fn:compare($parse-version($current), $parse-version($target)) >= 0
};'

if content.include?(old_func)
  new_content = content.sub(old_func, new_func)
  File.write('deploy/lib/xquery/setup.xqy', new_content)
  puts "SUCCESS: setup.xqy has been fixed!"
else
  puts "ERROR: Could not find the old function text."
  idx = content.index("declare function setup:at-least-version")
  puts "Function found at position: #{idx}"
  puts content[idx, 200]
end
