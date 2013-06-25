# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
#
# This file is part of Melange.
#
# Melange is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Melange is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Melange.  If not, see <http://www.gnu.org/licenses/>.

### Module to check item variables for special conditions

import json
import re

import requests

from flask import Blueprint, abort, make_response, request, render_template

from melange import app
from melange.auth import session_auth

updates = Blueprint('updates', __name__, template_folder='templates')

def item_plugin(item, *args):
    val = render_template('item_updates.html', item=item)
    return val

@updates.route('/api/<item_name>/')
@session_auth
def list_updates(item_name):
    ansible_url = app.config['ANSIBLE_URL']
    auth = ('melange', app.config['ANSIBLE_KEY'])
    r = requests.get('%s/modules/list_updates/?subset=%s'%(ansible_url, item_name), auth=auth)
    if r.status_code != 200:
        abort(400)
    data = r.json()
    if item_name not in data['contacted']:
        abort(400)

    installed = data['contacted'][item_name]['installed']
    updates = data['contacted'][item_name]['updates']

    val = {
        'installed': installed,
        'updates': updates,
    }

    response = make_response(json.dumps(val), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
