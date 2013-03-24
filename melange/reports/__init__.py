### Module to check item variables for special conditions

import re

from flask import Blueprint, request, render_template

from melange import Tag
from melange.auth import session_auth

reports = Blueprint('reports', __name__, template_folder='templates')

menu_items = {
    'Reports': 'reports.check_items'
}

@reports.route('/')
@session_auth
def check_items():
    tag_names = [ tag_name.strip() for tag_name in request.args.get('check-tags','').split(',') ]
    variable_name = request.args.get('check-variable', '')
    condition = request.args.get('check-condition', '')

    items = {}
    for tag_name in tag_names:
        tag = Tag.find(tag_name)
        if not tag:
            continue
        for item in tag.items:
            if item.name not in items:
                items[item.name] = item

    results = {}
    for item in items.values():
        variables = item.get_all_variables()
        if variable_name and variable_name in variables:
            if condition:
                if not re.search(condition, variables[variable_name]):
                    continue
            results[item.name] = variables[variable_name]

    return render_template('check.html', results=results, tags=tag_names, variable_name=variable_name, condition=condition)
