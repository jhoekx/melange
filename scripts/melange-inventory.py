#!/usr/bin/env python
# Ansible external inventory for Melange

# Copyright (C) 2012  Jeroen Hoekx <jeroen.hoekx@dsquare.be>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import json
import os
import sys

from optparse import OptionParser

import requests

CONFIG_FILE = 'melange-inventory.ini'

global MELANGE_URL
global MELANGE_AUTH

class Group(object):
    @staticmethod
    def all():
        groups = []
        resp = requests.get('%s/api/tag_items/'%(MELANGE_URL), auth=MELANGE_AUTH)
        data = json.loads(resp.text)
        for group_data in data:
            group = Group(group_data['name'], group_data['href'], group_data)
            groups.append(group)
        return groups

    def __init__(self, name, url, data=None):
        self.name = name
        self.url = '%s%s'%(MELANGE_URL, url)
        self.__hosts = []
        self.__data = data
    def __repr__(self):
        return "<Group ('%s')>"%(self.name)

    @property
    def data(self):
        if not self.__data:
            resp = requests.get(self.url, auth=MELANGE_AUTH)
            self.__data = json.loads(resp.text)
        return self.__data

    @property
    def hosts(self):
        if not self.__hosts:
            for host_data in self.data['items']:
                host = Host(host_data['name'], host_data['href'])
                self.__hosts.append(host)
        return self.__hosts

    @property
    def aliases(self):
        if 'aliases' in self.data['vars']:
            return self.data['vars']['aliases']
        else:
            return []

class Host(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
    def __repr__(self):
        return "<Host ('%s')>"%(self.name)


    @property
    def vars(self):
        vars = {}
        resp = requests.get(self.url, auth=MELANGE_AUTH)
        data = json.loads(resp.text)
        for var in data['vars']:
            vars[var['key']] = var['value']
        return vars

if __name__=="__main__":

    if not os.path.exists(CONFIG_FILE):
        print 'Configuration file "%s" does not exist.'%(CONFIG_FILE)
        sys.exit(1)

    cp = ConfigParser.ConfigParser()
    cp.read(CONFIG_FILE)
    MELANGE_URL = cp.get('inventory', 'MELANGE_URL')
    MELANGE_AUTH = (cp.get('inventory', 'MELANGE_USER'), cp.get('inventory', 'MELANGE_PASSWORD'))

    parser = OptionParser()
    parser.add_option('-l', '--list', default=False, dest="list_hosts", action="store_true")
    parser.add_option('-H', '--host', default=None, dest="host")
    parser.add_option('-e', '--extra-vars', default=None, dest="extra")
    options, args = parser.parse_args()

    if options.list_hosts == True:
        groups = Group.all()
        linux_group = [group for group in groups if group.name=='linux'][0]
        linux_hosts = [ host.name for host in linux_group.hosts ]
        result = {}
        for group in groups:
            result[group.name] = [host.name for host in group.hosts if host.name in linux_hosts]
            for alias in group.aliases:
                result[alias] = result[group.name]
        print json.dumps(result)
        sys.exit(0)

    if options.host is not None:
        result = {}
        host = Host(options.host, '%s/api/item/%s/'%(MELANGE_URL, options.host))
        result = host.vars
        if options.extra:
            k,v = options.extra.split("=")
            result[k] = v
        print json.dumps(result)
        sys.exit(0)
