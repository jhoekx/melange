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
elif 'MELANGE_CONFIG_ENVIRON' in os.environ:
    app.config.from_object('melange.config.EnvironmentConfig')
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

from melange.reports import reports
app.register_blueprint(reports, url_prefix='/reports')

@app.teardown_request
def shutdown_session(exception=None):
    db_session.close()
