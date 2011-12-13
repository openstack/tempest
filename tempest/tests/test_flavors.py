from nose.plugins.attrib import attr
from tempest import openstack
import unittest2 as unittest


class FlavorsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.flavors_client
        cls.config = cls.os.config
        cls.flavor_id = cls.config.env.flavor_ref

    @attr(type='smoke')
    def test_list_flavors(self):
        """List of all flavors should contain the expected flavor"""
        resp, body = self.client.list_flavors()
        flavors = body['flavors']

        resp, flavor = self.client.get_flavor_details(self.flavor_id)
        flavor_min_detail = {'id': flavor['id'], 'links': flavor['links'],
                             'name': flavor['name']}
        self.assertTrue(flavor_min_detail in flavors)

    @attr(type='smoke')
    def test_list_flavors_with_detail(self):
        """Detailed list of all flavors should contain the expected flavor"""
        resp, body = self.client.list_flavors_with_detail()
        flavors = body['flavors']
        resp, flavor = self.client.get_flavor_details(self.flavor_id)
        self.assertTrue(flavor in flavors)

    @attr(type='smoke')
    def test_get_flavor(self):
        """The expected flavor details should be returned"""
        resp, flavor = self.client.get_flavor_details(self.flavor_id)
        self.assertEqual(self.flavor_id, str(flavor['id']))
