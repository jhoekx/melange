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

import json

from flask import Blueprint, abort, redirect, request, url_for, make_response

from melange import Item, Tag, MelangeException
from melange.auth import basic_auth, session_auth_test

melange_api = Blueprint('melange_api', __name__)

@melange_api.route('/', methods=['GET'])
def start():
    return redirect(url_for('melange_api.list_tags'))

@melange_api.route('/item/<name>/', methods=['GET', 'PUT', 'DELETE'])
@session_auth_test
@basic_auth
def show_item(name):
    item = Item.find(name)
    if not item:
        abort(404)

    if request.method == 'DELETE':
        item.remove()
        response = make_response('', 200)
        return response

    if request.method == 'PUT':
        if not request.json:
            abort(415)
        try:
            if request.json['name'] != item.name:
                abort(400)
            item.update_from(request.json)
            item.save()
        except MelangeException:
            abort(400)

    def item_url(item):
        return url_for('melange_api.show_item', name=item.name)
    def tag_url(tag):
        return url_for('melange_api.show_tag', name=tag.name)
    data = item.to_data(item_href=item_url, tag_href=tag_url)

    response = make_response( json.dumps(data), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response

@melange_api.route('/tag/', methods=['GET', 'POST'])
@session_auth_test
@basic_auth
def list_tags():
    if request.method == 'POST':
        if not request.json:
            abort(415)
        data = request.json
        if not 'name' in data:
            abort(400)
        if Tag.find(data['name']):
            abort(409)
        tag = Tag(data['name'])
        try:
            tag.update_from(data)
        except MelangeException:
            abort(400)
        tag.save()
        response = make_response('', 201)
        response.headers['Content-Location'] = url_for('melange_api.show_tag',name=tag.name)
        return response

    tags = [ {'name':tag.name, 'href':url_for('melange_api.show_tag', name=tag.name)} for tag in Tag.find_all() ]

    response = make_response( json.dumps(tags), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response

@melange_api.route('/tag_items/', methods=['GET'])
@session_auth_test
@basic_auth
def tag_items():
    def item_url(item):
        return url_for('melange_api.show_item', name=item.name)
    tags = [tag.to_data(item_href=item_url) for tag in Tag.find_all()]

    response = make_response( json.dumps(tags), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response

@melange_api.route('/tag/<name>/', methods=['GET', 'POST', 'DELETE', 'PUT'])
@session_auth_test
@basic_auth
def show_tag(name):
    tag = Tag.find(name)
    if not tag:
        abort(404)

    if request.method == 'POST':
        if not request.json:
            abort(415)
        data = request.json
        if not 'name' in data:
            abort(400)
        response_code = 200
        item = Item.find(data['name'])
        if not item:
            item = Item(data['name'])
            response_code = 201
        try:
            item.update_from(data)
        except MelangeException:
            abort(400)
        item.add_to(tag)
        item.save()
        response = make_response('', response_code)
        response.headers['Content-Location'] = url_for('melange_api.show_item',name=item.name)
        return response

    if request.method == 'DELETE':
        tag.remove()
        response = make_response('', 200)
        return response

    if request.method == 'PUT':
        if not request.json:
            abort(415)
        try:
            if request.json['name'] != tag.name:
                abort(400)
            tag.update_from(request.json)
            tag.save()
        except MelangeException:
            abort(400)

    def item_url(item):
        return url_for('melange_api.show_item', name=item.name)
    data = tag.to_data(item_href=item_url)

    response = make_response( json.dumps(data), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response
