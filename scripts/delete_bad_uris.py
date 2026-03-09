import requests
from requests.auth import HTTPDigestAuth

auth    = HTTPDigestAuth('admin', 'admin123')
url     = 'http://localhost:8000/v1/eval'
deleted = 0

# Get all URIs that are not seed documents clm-0001 through clm-0010
raw = requests.post(url, data={
    'xquery': 'cts:uris()',
    'database': 'roxy-content'
}, auth=auth).text

uris = [l.strip() for l in raw.splitlines()
        if l.strip() and not l.strip().startswith('--')
        and not l.strip().startswith('Content')
        and not l.strip().startswith('X-')]

seed = ['/claims/clm-{:04d}.json'.format(i) for i in range(1, 11)]

for uri in uris:
    if uri not in seed:
        xq = 'xdmp:document-delete("' + uri + '")'
        r  = requests.post(url, data={'xquery': xq, 'database': 'roxy-content'}, auth=auth)
        if r.status_code == 200:
            deleted += 1

print('Deleted:', deleted)
