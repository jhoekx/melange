#!/usr/bin/env python
### Import data in JSON format

import json
import sys

from optparse import OptionParser
from urlparse import urljoin

import requests

parser = OptionParser()
parser.add_option('-d', '--dest', default=None, dest='url')
parser.add_option('-u', '--user', default=None, dest='user')
parser.add_option('-p', '--password', default=None, dest='password')
parser.add_option('-o', '--overwite', default=None, action='store_true', dest='overwite')
parser.add_option('-m', '--merge', default=None, action='store_true', dest='merge')
options, args = parser.parse_args()

def error(msg):
    print >>sys.stderr, msg
    sys.exit(1)

s = requests.Session()
s.headers.update({'Content-Type':'application/json'})

r = s.get(options.url)
if r.status_code == 401:
    if not options.user or not options.password:
        error('User and password required')
    s.auth = (options.user, options.password)

    r = s.get(options.url)

if r.status_code != 200:
    error('Unable to reach API: %s'%(r.status_code))
if not r.json:
    error('No JSON returned. Make sure you connect to the API.')

entry_url = r.url
existing_tags = {}
for tag_ref in r.json():
    existing_tags[tag_ref['name']] = urljoin(entry_url, tag_ref['href'])

json_text = ""
json_text = sys.stdin.read()

json_data = json.loads(json_text)

for tag_data in json_data['tags']:
    if tag_data['name'] in existing_tags:
        r = s.put(existing_tags[tag_data['name']], data=json.dumps(tag_data))
        if r.status_code >= 400:
            error('Failed to update tag <%s>'%(tag_data['name']))
    else:
        r = s.post(entry_url, data=json.dumps(tag_data))
        if r.status_code >= 400:
            error('Failed to create tag <%s>'%(tag_data['name']))
        existing_tags[tag_data['name']] = urljoin(entry_url, r.headers['Content-Location'])

children_cache = {}
for item_data in json_data['items']:
    first_tag_url = existing_tags[item_data['tags'][0]['name']]
    children = item_data.get('children', None)
    if children is not None:
        del item_data['children']

    r = s.post(first_tag_url, json.dumps(item_data))
    if r.status_code >= 400:
        error('Failed to create item <%s>'%(item_data['name']))
    if children is not None:
        children_cache[r.headers['Content-Location']] = children

for url, children in children_cache.items():
    r = s.get(urljoin(entry_url, url))
    item_data = r.json()
    item_data['children'] = children
    r = s.put(urljoin(entry_url, url), json.dumps(item_data))
    if r.status_code >= 400:
        error('Failed to update children for <%s>'%(item_data['name']))
