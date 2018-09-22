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

from functools import wraps

from flask import Blueprint, abort, g, redirect, request, session, url_for, make_response, render_template
from passlib.hash import sha256_crypt

from melange import User

user_auth = Blueprint('user_auth', __name__, template_folder='templates')


def session_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not 'username' in session:
            session['url'] = request.url
            return redirect(url_for('user_auth.login'))
        g.authenticated = True
        return f(*args, **kwargs)
    return decorated


def session_auth_test(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            g.authenticated = True
        return f(*args, **kwargs)
    return decorated


def basic_auth(f):
    def check_auth(auth):
        user = User.find(auth.username)
        if not user or not user.authenticate(auth.password):
            return False
        return True

    @wraps(f)
    def decorated(*args, **kwargs):
        if hasattr(g, 'authenticated') and g.authenticated:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not check_auth(auth):
            resp = make_response('Authentication Required', 401)
            resp.headers['WWW-Authenticate'] = 'Basic realm="Login required"'
            return resp
        g.authenticated = True
        return f(*args, **kwargs)
    return decorated


@user_auth.route('/', methods=['GET', 'POST'])
@session_auth
def list_users():
    if request.method == 'POST':
        if 'add-user' in request.form:
            user_name = request.form['user-name']
            user_password = request.form['user-password']
            user = User.find(user_name)
            if not user:
                user = User(user_name)
                user.password = user_password
                user.save()
    users = User.find_all()
    return render_template('users.html', users=users)


@user_auth.route('/user/<name>', methods=['GET', 'POST'])
@session_auth
def show_user(name):
    user = User.find(name)
    if request.method == 'POST':
        if 'remove-user' in request.form:
            user.remove()
            return redirect(url_for('.list_users'))
        elif 'change-password' in request.form:
            user_password = request.form['user-password']
            user.password = user_password
            user.save()
    return render_template('user.html', user=user)


@user_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form['user-name']
        user_password = request.form['user-password']
        user = User.find(user_name)
        if user and user.authenticate(user_password):
            session['username'] = user_name
        return redirect(session['url'])
    return render_template('login.html')


@user_auth.route('/logout', methods=['POST'])
def logout():
    session.pop('username')
    return redirect(url_for('show_frontpage'))
