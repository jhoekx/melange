import base64
import os
import unittest

from flask import url_for

os.environ['MELANGE_CONFIG_MODULE'] = 'melange.config.TestingConfig'

import melange
from melange import Item, Tag, User, app, db_session


def get_auth_headers():
    credentials = base64.b64encode(b'api:test').decode()
    return {
        'Authorization': f'Basic {credentials}'
    }


class MelangeTestCase(unittest.TestCase):

    def setUp(self):
        melange.database.drop_db()
        melange.database.init_db()

        user = User('api')
        user.password = 'test'
        user.save()

    def tearDown(self):
        pass

    def get_json(self, test_client, url):
        return test_client.get(url, headers=get_auth_headers())

    def post_json(self, test_client, url, data):
        return test_client.post(
            url,
            content_type='application/json',
            headers=get_auth_headers(),
            json=data,
        )

    def put_json(self, test_client, url, data):
        return test_client.put(
            url,
            content_type='application/json',
            headers=get_auth_headers(),
            json=data,
        )

    def delete_json(self, test_client, url):
        return test_client.get(url, headers=get_auth_headers())

    def test_api_create_tag(self):
        data = {
            'name': 'laptop'
        }
        with app.test_client() as c:
            rv = self.post_json(c, '/api/tag/', data)
            print(rv)
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
            print(rv)
            assert rv.status_code == 201
        fireflash = Item.find('fireflash')
        assert fireflash is not None
        assert fireflash.name == 'fireflash'
        assert len(fireflash.tags) == 1
        assert fireflash.tags[0].name == 'laptop'

    def test_api_remove_item(self):
        Tag('laptop').save()
        data = {'name': 'fireflash'}
        with app.test_client() as c:
            rv = self.post_json(c, '/api/tag/laptop/', data)
            assert rv.status_code == 201
            rv = self.delete_json(c, '/api/item/fireflash/')
            assert rv.status_code == 200

    def test_api_add_tag(self):
        Item('fireflash').save()
        Tag('laptop').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = rv.get_json()
            data['tags'].append({'name': 'laptop'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
            assert rv.status_code == 200
        laptop = Tag.find('laptop')
        assert laptop.items[0].name == 'fireflash'

    def test_api_add_child(self):
        Item('home').save()
        Item('fireflash').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/home/')
            data = rv.get_json()
            data['children'].append({'name': 'fireflash'})
            rv = self.put_json(c, '/api/item/home/', data)
            print(rv)
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        home = Item.find('home')
        assert fireflash.parents[0].name == 'home'
        assert home.children[0].name == 'fireflash'

    def test_api_incorrect_item_update(self):
        Item('fireflash').save()
        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = rv.get_json()
            data['name'] = 'hood'
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
            assert rv.status_code == 400

    def test_api_incorrect_tag_update(self):
        Tag('laptop').save()
        with app.test_client() as c:
            rv = self.get_json(c, '/api/tag/laptop/')
            data = rv.get_json()
            data['name'] = 'desktop'
            rv = self.put_json(c, '/api/tag/laptop/', data)
            print(rv)
            assert rv.status_code == 400

    def test_api_set_variable(self):
        Item('fireflash').save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = rv.get_json()
            data['vars'].append({'key': 'hello', 'value': 'world'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert fireflash.variables['hello'] == 'world'

    def test_api_add_variable(self):
        fireflash = Item('fireflash')
        fireflash.set_variable('test', 'one')
        fireflash.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = rv.get_json()
            data['vars'].append({'key': 'hello', 'value': 'world'})
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
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
            data = rv.get_json()
            data['vars'] = [{'key': 'test', 'value': 'one'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        assert len(fireflash.variables) == 1

    def test_api_update_variable(self):
        fireflash = Item('fireflash')
        fireflash.set_variable('test', 'one')
        fireflash.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/item/fireflash/')
            data = rv.get_json()
            data['vars'] = [{'key': 'test', 'value': 'two'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
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
            data = rv.get_json()
            data['vars']['test'] = 'two'
            rv = self.put_json(c, '/api/tag/laptop/', data)
            print(rv)
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
            data = rv.get_json()
            print(data)
            data['vars'] = [{'key': 'test', 'value': 'two'}]
            rv = self.put_json(c, '/api/item/fireflash/', data)
            print(rv)
            assert rv.status_code == 200
        fireflash = Item.find('fireflash')
        laptop = Tag.find('laptop')
        assert laptop.variables['test'] == 'one'
        assert fireflash.variables['test'] == 'two'
        assert fireflash.get_all_variables()['test'] == 'two'

    def test_ansible_inventory(self):
        fireflash = Item('fireflash')
        linux = Tag('linux')
        linux.set_variable('test', 'one')
        fireflash.add_to(linux)
        linux.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/ansible_inventory/')
            data = rv.get_json()
            assert rv.status_code == 200
            print(data)
            assert data == {
                'linux': {'hosts': ['fireflash']},
                '_meta': {'hostvars': {'fireflash': {'test': 'one'}}}
            }

    def test_ansible_inventory_default_tags(self):
        fireflash = Item('fireflash')
        mole = Item('mole')
        fab1 = Item('fab1')
        linux = Tag('linux')
        ansible = Tag('ansible-managed')
        windows = Tag('windows')
        multiple = Tag('multiple')
        fireflash.add_to(linux)
        mole.add_to(ansible)
        fab1.add_to(windows)
        fireflash.add_to(multiple)
        fab1.add_to(multiple)
        linux.save()
        ansible.save()
        windows.save()
        multiple.save()

        with app.test_client() as c:
            rv = self.get_json(c, '/api/ansible_inventory/')
            data = rv.get_json()
            assert rv.status_code == 200
            print(data)
            assert data == {
                'linux': {'hosts': ['fireflash']},
                'ansible-managed': {'hosts': ['mole']},
                'windows': {'hosts': []},
                'multiple': {'hosts': ['fireflash']},
                '_meta': {'hostvars': {'fireflash': {}, 'mole': {}}}
            }


if __name__ == '__main__':
    unittest.main()
