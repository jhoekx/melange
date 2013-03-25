
import importlib
import os

from flask import Flask

class MelangeException(Exception):
    pass

app = Flask('melange')
app.config.from_object('melange.config.ProductionConfig')
if 'MELANGE_CONFIG_MODULE' in os.environ:
    app.config.from_object(os.environ.get('MELANGE_CONFIG_MODULE'))
elif 'MELANGE_CONFIG_FILE' in os.environ:
    app.config.from_envvar('MELANGE_CONFIG_FILE')
else:
    app.config.from_object('melange.config.DevelopmentConfig')

from melange.database import db_session
from melange.models import Item, Tag, User, Log

import melange.filters
import melange.views

from melange.auth import user_auth
app.register_blueprint(user_auth, url_prefix='/auth')

from melange.api import melange_api
app.register_blueprint(melange_api, url_prefix='/api')

@app.teardown_request
def shutdown_session(exception=None):
    db_session.close()

app.config['menu_items'] = []

for plugin_data in app.config.get('PLUGINS', []):
    plugin_module = importlib.import_module(plugin_data['module'])
    if 'blueprint' in plugin_data and 'blueprint_url' in plugin_data:
        blueprint = getattr(plugin_module, plugin_data['blueprint'])
        app.register_blueprint(blueprint, url_prefix=plugin_data['blueprint_url'])
    if hasattr(plugin_module, 'menu_items'):
        menu_items = getattr(plugin_module, 'menu_items')
        app.config['menu_items'].append(menu_items)
