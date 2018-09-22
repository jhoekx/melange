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
from datetime import datetime, timedelta

from flask import (abort, g, make_response, redirect, render_template, request,
                   url_for)

from melange import Item, Log, Tag, app
from melange.auth import session_auth


def update_variables(item, request):
    if "var-add" in request.form:
        var_key = request.form['var-key']
        var_type = request.form['var-type']
        if var_type == 'List':
            item.set_variable(var_key, [''])
        elif var_type == 'Map':
            item.set_variable(var_key, {'': ''})
        else:
            item.set_variable(var_key, '')
        item.save()
        g.focus_variable = var_key
    elif "var-remove" in request.form:
        k = request.form['var-key']
        item.remove_variable(k)
        item.save()
    elif "var-text-save" in request.form:
        k = request.form['var-key']
        v = request.form['var-value']
        item.set_variable(k, v)
        item.save()
    elif 'var-list-add' in request.form:
        k = request.form['var-key']
        v = item.variables[k]
        v.append('')
        item.set_variable(k, v)
        item.save()
        g.focus_variable = k
    elif 'var-list-save' in request.form:
        k = request.form['var-key']
        item.set_variable(k, request.form.getlist('var-value[]'))
        item.save()
    elif 'var-list-remove' in request.form:
        k = request.form['var-key']
        items = item.variables[k]
        to_remove = sorted(
            [int(index) for index in request.form.getlist('var-select[]')], reverse=True)
        for index in to_remove:
            del items[index-1]
        item.set_variable(k, items)
        item.save()
    elif 'var-map-add' in request.form:
        key = request.form['var-key']
        map = item.variables[key]
        map[''] = ''
        item.set_variable(key, map)
        item.save()
        g.focus_variable = key
    elif 'var-map-save' in request.form:
        key = request.form['var-key']
        keys = request.form.getlist('var-value-key[]')
        values = request.form.getlist('var-value-value[]')
        map = {}
        for k, v in zip(keys, values):
            map[k] = v
        item.set_variable(key, map)
        item.save()
    elif 'var-map-remove' in request.form:
        key = request.form['var-key']
        map = item.variables[key]
        to_remove = request.form.getlist('var-select[]')
        for k in to_remove:
            del map[k]
        item.set_variable(key, map)
        item.save()


@app.route("/")
@session_auth
def show_frontpage():
    return render_template('front.html', tags=Tag.find_all())


@app.route("/tag/", methods=["GET", "POST"])
@session_auth
def list_tags():
    if request.method == "POST":
        tag_name = request.form["tag-name"]
        tag = Tag.find(tag_name)
        if not tag:
            tag = Tag(tag_name)
            tag.save()
    tags = Tag.find_all()
    return render_template('tags.html', tags=tags)


@app.route("/tag/<name>/", methods=["GET", "POST"])
@session_auth
def show_tag(name):
    tag = Tag.find(name)

    if request.method == "POST":
        if "tag-remove" in request.form:
            tag.remove()
            return redirect(url_for("list_tags"))
        else:
            update_variables(tag, request)

    var_list = []
    for k, v in tag.variables.items():
        if type(v) in [str, int]:
            var_type = 'Text'
        elif type(v) == list:
            var_type = 'List'
        elif type(v) == dict:
            var_type = 'Map'
        var_list.append({
            'key': k,
            'value': v,
            'type': var_type,
        })
    return render_template("tag.html", tag=tag, var_list=var_list)


@app.route("/item/", methods=["GET", "POST"])
@session_auth
def list_items():
    if request.method == "POST":
        item_name = request.form["item-name"]
        item = Item.find(item_name)
        if not item:
            item = Item(item_name)
        if 'tag-name' in request.form:
            tag = Tag.find(request.form['tag-name'])
            if tag:
                item.add_to(tag)
        item.save()
        return redirect(url_for('show_item', name=item.name))
    items = Item.find_all()
    return render_template('items.html', items=items)


@app.route("/item/<name>/", methods=["GET", "POST", "DELETE"])
@session_auth
def show_item(name):
    item = Item.find(name)
    if not item:
        abort(404)

    if request.method in ["POST", "DELETE"]:
        if "tag-add" in request.form:
            tag_name = request.form['tag-name']
            tag = Tag.find(tag_name)
            item.add_to(tag)
            item.save()
        elif "tag-remove" in request.form:
            tag_name = request.form['tag-name']
            tag = Tag.find(tag_name)
            item.remove_from(tag)
            item.save()
        elif "child-add" in request.form:
            child_name = request.form['child-name']
            child_item = Item.find(child_name)
            item.add_child(child_item)
            item.save()
        elif "child-remove" in request.form:
            child_name = request.form['child-name']
            child_item = Item.find(child_name)
            item.remove_child(child_item)
            item.save()
        elif "item-remove" in request.form:
            item.remove()
            return redirect(url_for("list_tags"))
        else:
            update_variables(item, request)

    var_list = []
    for var in item.to_data()['vars']:
        v = var['value']
        if type(v) in [str, int]:
            var['type'] = 'Text'
        elif type(v) == list:
            var['type'] = 'List'
        elif type(v) == dict:
            var['type'] = 'Map'
        var_list.append(var)

    tag_names = [tag.name for tag in item.tags]
    available_tags = [tag.name for tag in Tag.find_all()
                      if tag.name not in tag_names]

    return render_template('item.html', item=item, var_list=var_list, available_tags=available_tags)


@app.route('/log/')
@session_auth
def show_log():
    end = request.args.get('log-end')
    if end:
        end = datetime.strptime(end, '%Y-%m-%d')
    else:
        end = datetime.utcnow()
    start = request.args.get('log-start')
    if start:
        start = datetime.strptime(start, '%Y-%m-%d')
    else:
        start = end - timedelta(weeks=3)
    log = Log.find_range(start, end+timedelta(days=1))
    return render_template('log.html', log=log, start=start, end=end)
