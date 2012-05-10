import unittest2 as unittest

import nose

from tempest import openstack
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests import utils


class RolesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.AdminManager()
        cls.client = cls.os.admin_client
        cls.config = cls.os.config

        if not cls.client.has_admin_extensions():
            raise nose.SkipTest("Admin extensions disabled")

        cls.roles = []
        for _ in xrange(5):
            resp, body = cls.client.create_role(rand_name('role-'))
            cls.roles.append(body['id'])

    @classmethod
    def tearDownClass(cls):
        for role in cls.roles:
            cls.client.delete_role(role)

    def test_list_roles(self):
        """Return a list of all roles"""
        resp, body = self.client.list_roles()
        found = [role for role in body if role['id'] in self.roles]
        self.assertTrue(any(found))
        self.assertEqual(len(found), len(self.roles))

    def test_role_create_delete(self):
        """Role should be created, verified, and deleted"""
        role_name = rand_name('role-test-')
        resp, body = self.client.create_role(role_name)
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))
        self.assertEqual(role_name, body['name'])

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertTrue(any(found))

        resp, body = self.client.delete_role(found[0]['id'])
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertFalse(any(found))

    @unittest.skip('Until bug 997725 is fixed.')
    def test_role_create_blank_name(self):
        """Should not be able to create a role with a blank name"""
        try:
            resp, body = self.client.create_role('')
        except exceptions.Duplicate:
            self.fail('A role with a blank name already exists.')
        self.assertTrue('status' in resp)
        self.assertFalse(resp['status'].startswith('2'), 'Create role with '
                         'empty name should fail')

    def test_role_create_duplicate(self):
        """Role names should be unique"""
        role_name = rand_name('role-dup-')
        resp, body = self.client.create_role(role_name)
        role1_id = body.get('id')
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))

        try:
            resp, body = self.client.create_role(role_name)
            # this should raise an exception
            self.fail('Should not be able to create a duplicate role name.'
                      ' %s' % role_name)
        except exceptions.Duplicate:
            pass
        self.client.delete_role(role1_id)
