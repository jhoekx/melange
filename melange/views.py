
import json

from datetime import datetime, timedelta

from flask import abort, redirect, render_template, request, url_for, make_response

from melange import app, Item, Tag, Log
from melange.auth import session_auth

@app.route("/")
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
        if "var-add" in request.form or "var-update" in request.form:
            k = request.form['var-key']
            v = request.form['var-value']
            try:
                v = json.loads(v)
            except:
                pass
            tag.set_var(k, v)
            tag.save()
        elif "var-remove" in request.form:
            k = request.form['var-key']
            tag.remove_var(k)
            tag.save()
        elif "tag-remove" in request.form:
            tag.remove()
            return redirect(url_for("list_tags"))

    var_list = [ (k, json.dumps(v)) for k,v in tag.variables.items() ]
    return render_template("tag.html", tag=tag, vars=var_list)

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
        if "var-add" in request.form or "var-update" in request.form:
            k = request.form['var-key']
            v = request.form['var-value']
            try:
                v = json.loads(v)
            except:
                pass
            item.set_var(k, v)
            item.save()
        elif "var-remove" in request.form:
            k = request.form['var-key']
            item.remove_var(k)
            item.save()
        elif "tag-add" in request.form:
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

    var_list = [ (k, json.dumps(v)) for k,v in item.variables.items() ]

    tag_names = [ tag.name for tag in item.tags ]
    available_tags = [ tag.name for tag in Tag.find_all() if tag.name not in tag_names ]

    return render_template('item.html', item=item, vars=var_list, available_tags=available_tags)

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
        start =  end - timedelta(weeks=3)
    log = Log.find_range(start, end+timedelta(days=1))
    return render_template('log.html', log=log, start=start, end=end)
