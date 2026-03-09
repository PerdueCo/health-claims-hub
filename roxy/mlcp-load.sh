#!/bin/sh
CP=$(find /mlcp/lib -name '*.jar' | tr '\n' ':')
exec java -cp "$CP" com.marklogic.contentpump.ContentPump import \
  -host ml \
  -port 8041 \
  -username admin \
  -password admin123 \
  -input_file_path /bulk \
  -input_file_type documents \
  -document_type json \
  -output_uri_prefix /claims/ \
  -output_uri_replace "/bulk/,''" \
  -output_collections bulk-claims \
  -database roxy-content \
  -thread_count 4
