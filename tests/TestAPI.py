import base64
import json
import os
import unittest

from flask import url_for

os.environ['MELANGE_CONFIG_MODULE'] = 'melange.config.TestingConfig'

import melange
from melange import app, db_session, Item, Tag, User

class MelangeTestCase(unittest.TestCase):

    def setUp(self):
        melange.database.drop_db()
        melange.database.init_db()

        user = User('api')
        user.password = 'test'
        user.save()

    def tearDown(self):
        pass

    def get_json(self, c, url):
        return c.get(
            url,
            headers={'Authorization': 'Basic %s'%(base64.b64encode('api:test'))},
        )

    def post_json(self, c, url, data):
        return c.post(
            url,
            content_type='application/json',
            headers={'Authorization': 'Basic %s'%(base64.b64encode('api:test'))},
            data=json.dumps(data),
        )

    def put_json(self, c, url, data):
        return c.put(
            url,
            content_type='application/json',
            headers={'Authorization': 'Basic %s'%(base64.b64encode('api:test'))},
            data=json.dumps(data),
        )

    def test_api_create_tag(self):
        data = {
            'name': 'laptop'
        }
        with app.test_client() as c:
            rv = self.post_json(c, '/api/tag/', data)
            print rv
        laptop = Tag.find('laptop')
        assert laptop is not None
        assert laptop.name == 'laptop'

    def test_api_create_item(self):
        Tag('laptop').save()
        data = {
            'name': 'fireflash',
        }
        with app.test_client() as c:
            rv = self.post_json(c, '/api/tag/laptop/', data)
            print rv
            assert rv.status_code == 201
        fireflash = Item.find('fireflash')
        assert fireflash is not None
        assert fireflash.name == 'fireflash'
        assert len(fireflash.tags) == 1
        assert fireflash.tags[0].name == 'laptop'

    def test_api_add_tag(self):
        Item('fireflash').save()
        Tag('laptop').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['tags'].append({'name':'laptop'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        laptop = Tag.find('laptop')
        assert laptop.items[0].name == 'fireflash'

    def test_api_add_child(self):
        Item('home').save()
        Item('fireflash').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/home/')
            data = json.loads(rv.data)
            data['children'].append({'name':'fireflash'})
            rv = self.put_json(c, '/api/item/home/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        home = Item.find('home')
        assert fireflash.parents[0].name == 'home'
        assert home.children[0].name == 'fireflash'

    def test_api_incorrect_item_update(self):
        Item('fireflash').save()
        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['name'] = 'hood'
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 400

    def test_api_incorrect_tag_update(self):
        Tag('laptop').save()
        with app.test_client() as c:
            rv = self.get_json(c, '/api/tag/laptop/')
            data = json.loads(rv.data)
            data['name'] = 'desktop'
            rv = self.put_json(c, '/api/tag/laptop/', data)
            print rv
            assert rv.status_code == 400

    def test_api_set_variable(self):
        Item('fireflash').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['vars'].append({'key':'hello', 'value':'world'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert fireflash.variables['hello'] == 'world'

    def test_api_add_variable(self):
        fireflash = Item('fireflash')
        fireflash.set_variable('test', 'one')
        fireflash.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['vars'].append({'key':'hello', 'value':'world'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert fireflash.variables['hello'] == 'world'

    def test_api_remove_variable(self):
        fireflash = Item('fireflash')
        fireflash.set_variable('test', 'one')
        fireflash.set_variable('hello', 'world')
        fireflash.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['vars'] = [{'key':'test', 'value':'one'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert len(fireflash.variables) == 1

    def test_api_update_variable(self):
        fireflash = Item('fireflash')
        fireflash.set_variable('test', 'one')
        fireflash.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            data['vars'] = [{'key':'test', 'value':'two'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert fireflash.variables['test'] == 'two'

    def test_api_set_tag_variable(self):
        fireflash = Item('fireflash')
        laptop = Tag('laptop')
        laptop.set_variable('test', 'one')
        fireflash.add_to(laptop)
        laptop.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/tag/laptop/')
            data = json.loads(rv.data)
            data['vars']['test']= 'two'
            rv = self.put_json(c, '/api/tag/laptop/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        laptop = Tag.find('laptop')
        assert laptop.variables['test'] == 'two'
        assert fireflash.get_all_variables()['test'] == 'two'

    def test_api_override_tag_variable(self):
        fireflash = Item('fireflash')
        laptop = Tag('laptop')
        laptop.set_variable('test', 'one')
        fireflash.add_to(laptop)
        laptop.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = json.loads(rv.data)
            print data
            data['vars'] = [{'key':'test', 'value':'two'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print rv
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        laptop = Tag.find('laptop')
        assert laptop.variables['test'] == 'one'
        assert fireflash.variables['test'] == 'two'
        assert fireflash.get_all_variables()['test'] == 'two'

if __name__ == '__main__':
    unittest.main()
