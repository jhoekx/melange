#!/usr/bin/env python
### Export data in JSON format

import json
import sys

from optparse import OptionParser
from urlparse import urljoin

import requests

parser = OptionParser()
parser.add_option('-s', '--src', default=None, dest='url')
parser.add_option('-u', '--user', default=None, dest='user')
parser.add_option('-p', '--password', default=None, dest='password')
options, args = parser.parse_args()

def error(msg):
    print >>sys.stderr, msg
    sys.exit(1)

if not options.url:
    parser.print_help()
    sys.exit(1)

s = requests.Session()

r = s.get(options.url)
if r.status_code == 401:
    if not options.user or not options.password:
        error('User and password required')
    s.auth = (options.user, options.password)

    r = s.get(options.url)

if r.status_code != 200:
    error('Unable to reach API')
if not r.json:
    error('No JSON returned. Make sure you connect to the API.')

tags = []
item_urls = []
items = []

for tag_ref in r.json():
    tag_url = urljoin(options.url, tag_ref['href'])
    tag_req = s.get(tag_url)
    tag_data = tag_req.json()
    for item_data in tag_data['items']:
        item_url = urljoin(options.url, item_data['href'])
        if item_url not in item_urls:
            item_urls.append(item_url)
    del tag_data['items']
    tags.append(tag_data)

for item_url in item_urls:
    item_req = s.get(item_url)
    item_data = item_req.json()
    item_data['vars'] = [ var for var in item_data['vars'] if 'tag' not in var ]
    items.append(item_data)

print json.dumps({
    'tags': tags,
    'items': items,
})
