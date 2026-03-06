filepath = 'src/roxy/lib/rewriter-lib.xqy'
content = File.read(filepath)

# Fix the namespace mismatch - update to match what ML11 actually has
old_ns = '"http://marklogic.com/rest-api/endpoints/config"'
new_ns = '"http://marklogic.com/rest-api/endpoints/config_DELETE_IF_UNUSED"'

if content.include?(old_ns)
  new_content = content.sub(old_ns, new_ns)
  File.write(filepath, new_content)
  puts "SUCCESS: rewriter-lib.xqy has been fixed!"
else
  puts "ERROR: Could not find the namespace string."
  puts "Searching for 'config' in file..."
  content.each_line.with_index(1) do |line, i|
    puts "#{i}: #{line.strip}" if line.include?("config") && i < 20
  end
end
