### HTTP API to run Ansible playbooks

import glob
import json
import os
import shlex
import subprocess

from functools import wraps

from ansible.runner import Runner
from flask import Flask, Response, make_response, redirect, request, safe_join, url_for
from passlib.hash import sha256_crypt

app = Flask('ansible_api')

app.config['ANSIBLE_HOSTS'] = 'hosts'
app.config['ANSIBLE_PLAYBOOKS'] = 'playbooks'
app.config['ANSIBLE_MODULES'] = '/usr/share/ansible'
app.config['COMMON_KEY'] = 'abcdefgh'
if 'ANSIBLE_API_SETTINGS' in os.environ:
    app.config.from_envvar('ANSIBLE_API_SETTINGS')

def run_playbook(name):
    args = shlex.split("ansible-playbook %s -i %s"%(name, app.config['ANSIBLE_HOSTS']))
    p = subprocess.Popen(args, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for line in iter(p.stdout.readline,''):
        yield line
    p.wait()

def basic_auth(f):
    def check_auth(auth):
        return auth.password == app.config['COMMON_KEY']
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth):
            resp = make_response('Authentication Required',401)
            resp.headers['WWW-Authenticate'] = 'Basic realm="Login required"'
            return resp
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def main():
    return redirect(url_for('.list_playbooks'))

@app.route('/playbooks/', methods=['GET'])
def list_playbooks():
    playbook_path = os.path.abspath(app.config['ANSIBLE_PLAYBOOKS'])
    playbooks = []
    for path in glob.glob(os.path.join(playbook_path, '*.yml')):
        playbooks.append(path.rsplit('/',1)[1].replace('.yml', ''))

    data = []
    for playbook in playbooks:
        data.append({
            'name': playbook,
            'href': url_for('.show_playbook', name=playbook)
            })
    response = make_response(json.dumps(data), 200)
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/playbooks/<name>/', methods=['GET', 'POST'])
@basic_auth
def show_playbook(name):
    playbook_path = os.path.abspath(app.config['ANSIBLE_PLAYBOOKS'])
    playbook = safe_join(playbook_path, '%s.yml'%(name))

    return Response(run_playbook(playbook), mimetype='text/plain')

@app.route('/modules/<module_name>/', methods=['GET', 'POST'])
@basic_auth
def run_module(module_name):
    subset = request.args.get('subset')

    r = Runner(host_list=app.config['ANSIBLE_HOSTS'], module_name=module_name, subset=subset)
    res = r.run()

    response = make_response(json.dumps(res), 200)
    response.headers['Content-Type'] = 'text/plain'
    return response
