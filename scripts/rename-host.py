#!/usr/bin/env python

# Copyright (C) 2013  Jeroen Hoekx <jeroen.hoekx@dsquare.be>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Script to transfer inventory information from one host to another

import json
import sys
from optparse import OptionParser
from urllib.parse import urljoin

import requests

parser = OptionParser()
parser.add_option('-d', '--dest', default=None, dest='url')
parser.add_option('-u', '--user', default=None, dest='user')
parser.add_option('-p', '--password', default=None, dest='password')
parser.add_option('-f', '--from', default=None, dest='orig')
parser.add_option('-t', '--to', default=None, dest='to')
options, args = parser.parse_args()


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


if not options.orig:
    error('--from missing')
if not options.to:
    error('--to missing')

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})

r = s.get(options.url)
if r.status_code == 401:
    if not options.user or not options.password:
        error('User and password required')
    s.auth = (options.user, options.password)

    r = s.get(options.url)

r = s.get(urljoin(options.url, '/api/item/%s/' % (options.orig)))
if r.status_code > 400:
    error('Unable to find host %s' % (options.orig))

orig_data = r.json()

r = s.get(urljoin(options.url, '/api/item/%s/' % (options.to)))
if r.status_code > 400:
    error('Unable to find host %s' % (options.to))

orig_data['name'] = options.to

r = s.put(urljoin(options.url, '/api/item/%s/' %
                  (options.to)), data=json.dumps(orig_data))
if r.status_code > 400:
    error('Failed to update data of new system')

r = s.delete(urljoin(options.url, '/api/item/%s/' % (options.orig)))
if r.status_code > 400:
    error('Failed to remove old system.')
