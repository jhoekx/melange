
import json

from flask import Blueprint, abort, redirect, request, url_for, make_response

from melange import Item, Tag, MelangeException
from melange.auth import basic_auth, session_auth_test

melange_api = Blueprint('melange_api', __name__)

def update_item(item, json_data):
    ### normalize variables
    if type(json_data.get('vars', {}))==list:
        vars = {}
        own_vars = [ property for property in json_data['vars'] if 'tag' not in property ]
        for property in json_data['vars']:
            vars[property['key']] = property['value']
        for property in own_vars:
            vars[property['key']] = property['value']
        json_data['vars'] = vars

    ### tags
    current_tags = [ tag.name for tag in item.tags ]
    new_tags = [ tag['name'] for tag in json_data.get('tags', [])]
    tags_to_add = set(new_tags) - set(current_tags)
    tags_to_remove = set(current_tags) - set(new_tags)

    for tag_name in tags_to_add:
        tag = Tag.find(tag_name)
        if not tag:
            abort(400)
        item.add_to(tag)

    for tag_name in tags_to_remove:
        tag = Tag.find(tag_name)
        if tag:
            item.remove_from(tag)

    ### children
    current_children = [ child.name for child in item.children ]
    new_children = [ child['name'] for child in json_data.get('children', []) ]
    children_to_add = set(new_children) - set(current_children)
    children_to_remove = set(current_children) -  set(new_children)

    for child_name in children_to_add:
        child = Item.find(child_name)
        if not child:
            abort(400)
        item.add_child(child)

    for child_name in children_to_remove:
        child = Item.find(child_name)
        if child:
            item.remove_child(child)

    ### variables
    current_variables = item.variables
    all_variables = item.get_all_variables()
    new_variables = json_data.get('vars', {})
    for k,v in current_variables.items():
        if k not in new_variables:
            item.remove_variable(k)
        ### check existing variables later on
    for k,v in new_variables.items():
        if k not in all_variables:
            item.set_variable(k, v)
        else:
            if k in current_variables:
                if v != current_variables[k]:
                    item.set_variable(k, v)
            else:
                if v != all_variables[k]:
                    item.set_variable(k, v)

def update_tag(tag, json_data):
    ### items
    current_items = [ item.name for item in tag.items ]
    new_items = [ item['name'] for item in json_data.get('items', []) ]
    items_to_add = set(new_items) - set(current_items)
    items_to_remove = set(current_items) - set(new_items)

    for item_name in items_to_add:
        item = Item.find(item_name)
        if not item:
            abort(400)
        item.add_to(tag)
    for item_name in items_to_remove:
        item = Item.find(item_name)
        if item:
            item.remove_from(tag)

    ### variables
    current_variables = tag.variables
    new_variables = json_data.get('vars', {})
    for k,v in current_variables.items():
        if k not in new_variables:
            tag.remove_variable(k)
        else:
            if v!=new_variables[k]:
                tag.set_variable(k, new_variables[k])
    for k,v in new_variables.items():
        if k not in current_variables:
            tag.set_variable(k, v)
        ### existing variables are already checked

@melange_api.route('/', methods=['GET'])
def start():
    return redirect(url_for('melange_api.list_tags'))

@melange_api.route('/item/', methods=['GET', 'POST'])
@session_auth_test
@basic_auth
def list_items():
    if request.method == 'POST':
        if not request.json:
            abort(415)
        data = request.json
        if not 'name' in data:
            abort(400)
        if Item.find(data['name']):
            abort(409)
        item = Item(data['name'])
        try:
            update_item(item, data)
        except MelangeException:
            abort(400)
        item.save()
        response = make_response('', 201)
        response.headers['Content-Location'] = url_for('melange_api.show_item',name=item.name)
        return response
    items = [ {'name':item.name, 'href':url_for('melange_api.show_item', name=item.name)} for item in Item.find_all() ]

    response = make_response( json.dumps(items), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response

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
            update_item(item, request.json)
            item.save()
        except MelangeException:
            abort(400)

    vars = []
    var_keys = []
    def tag_sort(tag):
        return tag.name
    for tag in sorted(item.tags, key=tag_sort):
        for k,v in tag.variables.items():
            ### overwrite var if tag name is longer
            if k in var_keys:
                prev_var = [ var for var in vars if var['key']==k ][0]
                if len(tag.name) > len(prev_var['tag']):
                    vars.remove(prev_var)
                else:
                    continue
            vars.append({
                'key': k,
                'value': v,
                'tag': tag.name,
                'href': url_for('show_tag', name=tag.name)
            })
            var_keys.append(k)
    for k,v in item.variables.items():
        if k in var_keys:
            prev_var = [ var for var in vars if var['key']==k ][0]
            vars.remove(prev_var)
        vars.append({'key':k, 'value': v})
    def vars_sort(var):
        return var['key']
    vars = sorted(vars, key=vars_sort)

    data = {
        'name': item.name,
        'vars': vars,
        'tags': [ {'name':tag.name,'href':url_for('melange_api.show_tag',name=tag.name)} for tag in item.tags ],
        'children': [ {'name':child.name, 'href':url_for('melange_api.show_item',name=child.name)} for child in item.children ],
    }

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
            update_tag(tag, data)
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

@melange_api.route('/tag/<name>/', methods=['GET', 'DELETE', 'PUT'])
@session_auth_test
@basic_auth
def show_tag(name):
    tag = Tag.find(name)
    if not tag:
        abort(404)

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
            update_tag(tag, request.json)
            tag.save()
        except MelangeException:
            abort(400)

    data = {
        'name': tag.name,
        'vars': tag.get_variables(),
        'items': [ {'name':item.name, 'href':url_for('melange_api.show_item',name=item.name)} for item in tag.items ],
    }

    response = make_response( json.dumps(data), 200 )
    response.headers['Content-Type'] = 'application/json'
    return response
