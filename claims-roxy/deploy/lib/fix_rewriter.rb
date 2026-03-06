filepath = 'src/roxy/lib/rewriter-lib.xqy'
content = File.read(filepath)

old_import = 'import module namespace conf = "http://marklogic.com/rest-api/endpoints/config"
  at "/MarkLogic/rest-api/endpoints/config.xqy";'

new_import = 'import module namespace conf = "http://marklogic.com/rest-api/endpoints/config_DELETE_IF_UNUSED"
  at "/MarkLogic/rest-api/endpoints/config.xqy";'

if content.include?(old_import)
  new_content = content.sub(old_import, new_import)
  File.write(filepath, new_content)
  puts "SUCCESS: rewriter-lib.xqy has been fixed!"
else
  puts "ERROR: Could not find the old import. Showing line 4-7:"
  lines = content.split("\n")
  lines[3..6].each_with_index { |l, i| puts "#{i+4}: #{l}" }
end
