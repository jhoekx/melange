import os
import unittest

from datetime import datetime, timedelta

os.environ['MELANGE_CONFIG_MODULE'] = 'melange.config.TestingConfig'

import melange
from melange import db_session, Item, Tag, User, Log

class MelangeTestCase(unittest.TestCase):

    def setUp(self):
        self.app = melange.app.test_client()
        melange.database.drop_db()
        melange.database.init_db()

    def tearDown(self):
        pass

    def create_simple_setup(self):
        item = Item('firefly')
        db_session.add(item)
        db_session.commit()

        tag = Tag('laptop')
        db_session.add(tag)
        db_session.commit()

    def test_empty_items(self):
        assert(len(Item.query.all())==0)

    def test_empty_tags(self):
        assert(len(Tag.query.all())==0)

    def test_add_item(self):
        self.create_simple_setup()
        item = Item.query.filter(Item.name=='firefly').one()
        items = Item.query.all()
        assert item in items

    def test_add_tag_to_item(self):
        self.create_simple_setup()
        item = Item.query.filter(Item.name=='firefly').one()
        tag = Tag.query.filter(Tag.name=='laptop').one()

        item.tags.append(tag)
        db_session.add(item)
        db_session.commit()

        assert item in tag.items

    def test_remove_tag_from_item(self):
        self.test_add_tag_to_item()

        item = Item.query.filter(Item.name=='firefly').one()
        tag = Tag.query.filter(Tag.name=='laptop').one()
        item.tags.remove(tag)
        db_session.add(item)
        db_session.commit()

        assert item not in tag.items

    def test_item_variable(self):
        self.create_simple_setup()

        item = Item.query.filter(Item.name=='firefly').one()
        item.set_variable('hello', 'world')
        item.set_variable('mylist', ['a', 'b'])
        item.set_variable('mydict', {'hello': 'world'})
        db_session.add(item)
        db_session.commit()

        vars = item.variables
        assert vars['hello'] == 'world'
        assert vars['mylist'] == ['a', 'b']
        assert vars['mydict'] == {'hello': 'world'}

    def test_remove_item_variables(self):
        self.create_simple_setup()
        item = Item.query.filter(Item.name=='firefly').one()
        item.set_variable('hello', 'world')
        db_session.add(item)
        db_session.commit()

        item.remove_variable('hello')
        db_session.add(item)
        db_session.commit()

        assert 'hello' not in item.variables

    def test_tag_variable(self):
        self.create_simple_setup()

        item = Item.query.filter(Item.name=='firefly').one()
        tag = Tag.query.filter(Tag.name=='laptop').one()
        tag.set_variable('hello', 'world')
        tag.items.append(item)
        db_session.add(tag)
        db_session.commit()

        assert 'hello' not in item.variables
        assert 'hello' in item.get_all_variables()

    def test_duplicate_tag_variable(self):
        ''' variable in longest tag wins '''
        item = Item('firefly')
        laptop = Tag('laptop')
        laptop.set_variable('hello', 'laptop')
        linux = Tag('linux')
        linux.set_variable('hello', 'linux')
        item.add_to(laptop)
        item.add_to(linux)
        item.save()

        assert 'hello' in item.get_all_variables()
        assert item.get_all_variables()['hello'] == 'laptop'

    def test_avoid_duplicate_tag(self):
        self.create_simple_setup()

        item = Item.query.filter(Item.name=='firefly').one()
        tag = Tag.query.filter(Tag.name=='laptop').one()
        tag.items.append(item)
        db_session.add(tag)
        db_session.commit()

        tag.items.append(item)
        db_session.add(tag)
        db_session.commit()

        assert len(tag.items) == 1

    def test_parent_child(self):
        i1 = Item('firefly')
        i2 = Item('fireflash')
        i3 = Item('home')
        db_session.add(i1)
        db_session.add(i2)
        db_session.add(i3)
        db_session.commit()

        i3.children.append(i1)
        i3.children.append(i2)
        db_session.add(i3)
        db_session.commit()

        assert i3.children == [i1, i2]
        assert i1.parents == [i3]

    def test_data_variable_in_multiple_tags(self):
        item = Item('firefly')
        item.set_variable('hello', 'firefly')
        linux = Tag('linux')
        linux.set_variable('hello', 'linux')
        laptop = Tag('laptop')
        laptop.set_variable('hello', 'laptop')
        item.add_to(linux)
        item.add_to(laptop)
        item.save()

        data = item.to_data()
        hello = [entry['value'] for entry in data['vars'] if entry['key'] == 'hello']
        assert len(hello) == 1
        assert hello[0] == 'firefly'

class MelangeUserTestCase(unittest.TestCase):
    def setUp(self):
        melange.database.drop_db()
        melange.database.init_db()

    def test_user(self):
        admin = User('admin')
        admin.password = '123456'
        db_session.add(admin)
        db_session.commit()

        admin = User.query.filter(User.name=='admin').one()
        assert admin.authenticate('123456')
        assert admin.authenticate('12345') == False

class MelangeLogTestCase(unittest.TestCase):
    def setUp(self):
        melange.database.drop_db()
        melange.database.init_db()

    def test_log(self):
        log = Log('fireflash', 'test')
        db_session.add(log)
        db_session.commit()

        log = Log.query.filter(Log.name=='fireflash').one()
        assert log.message == 'test'

    def test_log_order(self):
        now = datetime.utcnow()
        earlier = now - timedelta(1)
        log2 = Log('firefly', 'test2', earlier)
        log1 = Log('fireflash', 'test1', now)
        db_session.add(log1)
        db_session.add(log2)
        db_session.commit()

        logs = Log.find_all()
        assert logs[0].message == 'test1'

    def test_log_range(self):
        now = datetime.utcnow()
        earlier = now - timedelta(1)
        log2 = Log('firefly', 'test2', earlier)
        log1 = Log('fireflash', 'test1', now)
        db_session.add(log1)
        db_session.add(log2)
        db_session.commit()

        logs = Log.find_range(now)
        assert len(logs)==1
        assert logs[0].message == 'test1'

    def test_log_on_item_insert(self):
        item = Item('fireflash')
        db_session.add(item)
        db_session.commit()

        logs = Log.find_all()
        assert len(logs) == 1
        assert logs[0].name == 'fireflash'

    def test_no_log_on_creation(self):
        item = Item('fireflash')
        db_session.add(item)
        db_session.rollback()

        logs = Log.find_all()
        assert len(logs) == 0

    def test_log_on_variable(self):
        item = Item('fireflash')
        item.set_variable('hello', 'world')
        db_session.add(item)
        db_session.commit()

        logs = Log.find_all()
        assert len(logs) == 2
        assert 'hello' in logs[0].message or 'hello' in logs[1].message

if __name__ == '__main__':
    unittest.main()
