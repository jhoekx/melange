
import json

from datetime import datetime

from passlib.hash import sha256_crypt
from sqlalchemy import Column, ForeignKey, DateTime, Integer, String, Text, Table
from sqlalchemy.orm import relationship

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
