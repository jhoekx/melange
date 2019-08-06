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

from datetime import datetime

from passlib.hash import sha256_crypt
from sqlalchemy import Column, ForeignKey, DateTime, Integer, String, Text, Table
from sqlalchemy.orm import relationship

from melange import MelangeException
from melange.database import Base, db_session

items_to_tags = Table('items_to_tags', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
)

items_to_items = Table('items_to_items', Base.metadata,
    Column('parent_id', Integer, ForeignKey('items.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('items.id'), primary_key=True),
)

class VariableMixin(object):
    def get_variables(self):
        if self.properties:
            return json.loads(self.properties)
        else:
            return {}
    variables = property(get_variables)

    def set_variable(self, key, value):
        vars = self.variables
        vars[key] = value
        self.properties = json.dumps(vars)
        self._log("Variable '%s' set to '%s'"%(key, value))

    def remove_variable(self, key):
        vars = self.variables
        del vars[key]
        self.properties = json.dumps(vars)
        self._log("Variable '%s' removed"%(key))

class CompatMixin(object):
    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find(cls, name):
        try:
            return cls.query.filter(cls.name==name).one()
        except:
            return None

    def save(self):
        db_session.add(self)
        db_session.commit()

    def remove(self):
        self._log('Removed')
        db_session.delete(self)
        db_session.commit()

class LogMixin(object):
    def _log(self, message):
        db_session.add( Log(self.name, message) )

class Item(Base, VariableMixin, CompatMixin, LogMixin):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    tags = relationship('Tag', secondary=items_to_tags, backref='items')
    properties = Column(Text)
    children = relationship('Item', secondary=items_to_items, primaryjoin=id==items_to_items.c.parent_id, secondaryjoin=id==items_to_items.c.child_id, backref='parents')

    def __init__(self, name):
        self.name = name
        self._log('Item created')
    def __repr__(self):
        return "<Item '%s'>"%(self.name)

    def get_all_variables(self):
        def tag_length(tag):
            return len(tag.name)
        vars = {}
        for tag in sorted(self.tags, key=tag_length):
            vars.update(tag.variables)
        vars.update(self.variables)
        return vars

    def add_to(self, tag):
        self.tags.append(tag)
        self._log('Tag %s added'%(tag.name))

    def remove_from(self, tag):
        self.tags.remove(tag)
        self._log('Tag %s removed'%(tag.name))

    def add_child(self, child):
        self.children.append(child)
        self._log('Child %s added'%(child.name))

    def remove_child(self, child):
        self.children.remove(child)
        self._log('Child %s removed'%(child.name))

    def to_data(self, item_href=None, tag_href=None):
        ''' Return a data representation of this Item.
            The vars attribute shows the origin of the variable.'''
        def tag_length(tag):
            return len(tag.name)
        def vars_sort(var):
            return var['key']
        data = {
            'name': self.name,
            'tags': [],
            'children': [],
        }
        for tag in self.tags:
            tag_data = {'name': tag.name}
            if tag_href:
                tag_data['href'] = tag_href(tag)
            data['tags'].append(tag_data)
        for child in self.children:
            child_data = {'name': child.name}
            if item_href:
                child_data['href'] = item_href(child)
            data['children'].append(child_data)
        vars = []
        var_keys = {}
        for tag in sorted(self.tags, key=tag_length):
            for k,v in tag.variables.items():
                var = {
                    'key': k,
                    'value': v,
                    'tag': tag.name
                }
                if tag_href:
                    var['href'] = tag_href(tag)
                if k in var_keys:
                    vars.remove(var_keys[k])
                    var_keys[k] = var
                else:
                    var_keys[k] = var
                vars.append(var)
        for k, v in self.variables.items():
            if k in var_keys:
                vars.remove(var_keys[k])
            vars.append({'key': k, 'value': v })
        data['vars'] = sorted(vars, key=vars_sort)
        return data

    def update_from(self, data):
        ### normalize variables
        if type(data.get('vars', {}))==list:
            vars = {}
            own_vars = [ property for property in data['vars'] if 'tag' not in property ]
            for property in data['vars']:
                vars[property['key']] = property['value']
            for property in own_vars:
                vars[property['key']] = property['value']
            data['vars'] = vars

        ### tags
        current_tags = [ tag.name for tag in self.tags ]
        new_tags = [ tag['name'] for tag in data.get('tags', [])]
        tags_to_add = set(new_tags) - set(current_tags)
        tags_to_remove = set(current_tags) - set(new_tags)

        for tag_name in tags_to_add:
            tag = Tag.find(tag_name)
            if not tag:
                raise MelangeException("Tag '%s' not found"%(tag_name))
            self.add_to(tag)

        for tag_name in tags_to_remove:
            tag = Tag.find(tag_name)
            if tag:
                self.remove_from(tag)

        ### children
        current_children = [ child.name for child in self.children ]
        new_children = [ child['name'] for child in data.get('children', []) ]
        children_to_add = set(new_children) - set(current_children)
        children_to_remove = set(current_children) -  set(new_children)

        for child_name in children_to_add:
            child = Item.find(child_name)
            if not child:
                raise MelangeException("Child '%s' not found"%(child_name))
            self.add_child(child)

        for child_name in children_to_remove:
            child = Item.find(child_name)
            if child:
                self.remove_child(child)

        ### variables
        current_variables = self.variables
        all_variables = self.get_all_variables()
        new_variables = data.get('vars', {})
        for k,v in current_variables.items():
            if k not in new_variables:
                self.remove_variable(k)
            ### check existing variables later on
        for k,v in new_variables.items():
            if k not in all_variables:
                self.set_variable(k, v)
            else:
                if k in current_variables:
                    if v != current_variables[k]:
                        self.set_variable(k, v)
                else:
                    if v != all_variables[k]:
                        self.set_variable(k, v)

class Tag(Base, VariableMixin, CompatMixin, LogMixin):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(), unique=True)
    properties = Column(Text)

    def __init__(self, name):
        self.name = name
        self._log('Tag %s created'%(self.name))
    def __repr__(self):
        return "<Tag '%s'>"%(self.name)

    def to_data(self, item_href=None):
        data = {
            'name': self.name,
            'items': [],
            'vars': self.variables,
        }
        for item in self.items:
            item_data = {'name': item.name}
            if item_href:
                item_data['href'] = item_href(item)
            data['items'].append(item_data)
        return data

    def update_from(self, data):
        ### items
        current_items = [ item.name for item in self.items ]
        new_items = [ item['name'] for item in data.get('items', []) ]
        items_to_add = set(new_items) - set(current_items)
        items_to_remove = set(current_items) - set(new_items)

        for item_name in items_to_add:
            item = Item.find(item_name)
            if not item:
                raise MelangeException("Item '%s' not found"%(item_name))
            item.add_to(self)
        for item_name in items_to_remove:
            item = Item.find(item_name)
            if item:
                item.remove_from(self)

        ### variables
        current_variables = self.variables
        new_variables = data.get('vars', {})
        for k,v in current_variables.items():
            if k not in new_variables:
                self.remove_variable(k)
            else:
                if v!=new_variables[k]:
                    self.set_variable(k, new_variables[k])
        for k,v in new_variables.items():
            if k not in current_variables:
                self.set_variable(k, v)
            ### existing variables are already checked

class User(Base, CompatMixin, LogMixin):
    __tablename__  = 'users'

    name = Column(String, primary_key=True)
    hash = Column(String)

    def __init__(self, name):
        self.name = name
        self._log('User %s created'%(self.name))
    def __repr__(self):
        return "<User('%s')>"%(self.name)

    def set_password(self, passwd):
        self.hash = sha256_crypt.encrypt(passwd)
        self._log('Password set')
    password = property(None,set_password)

    def authenticate(self, passwd):
        return sha256_crypt.verify(passwd, self.hash)

class Log(Base, CompatMixin):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    message = Column(Text, nullable=False)

    @classmethod
    def find_all(cls):
        return cls.query.order_by(cls.date.desc()).all()

    @classmethod
    def find_range(cls, start, end=None):
        if not end:
            end = datetime.utcnow()
        return cls.query.filter(cls.date>=start, cls.date<=end).order_by(cls.date.desc()).all()

    def __init__(self, name, message, date=None):
        if date is None:
            date = datetime.utcnow()
        self.name = name
        self.message = message
        self.date = date
    def __repr__(self):
        return "<Log('%s', '%s', '%s')"%(self.name, self.message, self.date)
