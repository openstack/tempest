from nose.plugins.attrib import attr
from nose import SkipTest
import tempest.config
from tempest import exceptions
from tempest import openstack
from tempest.tests.base_compute_test import BaseComputeTest


class FlavorsAdminTest(BaseComputeTest):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        cls.config = tempest.config.TempestConfig()
        cls.admin_username = cls.config.compute_admin.username
        cls.admin_password = cls.config.compute_admin.password
        cls.admin_tenant = cls.config.compute_admin.tenant_name

        if not(cls.admin_username and cls.admin_password and cls.admin_tenant):
            raise SkipTest("Missing Admin credentials in configuration")
        else:
            cls.admin_os = openstack.AdminManager()
            cls.admin_client = cls.admin_os.flavors_client
            cls.flavor_name = 'test_flavor'
            cls.ram = 512
            cls.vcpus = 1
            cls.disk = 10
            cls.ephemeral = 10
            cls.new_flavor_id = 1234
            cls.swap = 1024
            cls.rxtx = 1

    @attr(type='positive')
    def test_create_flavor(self):
        """Create a flavor and ensure it is listed
        This operation requires the user to have 'admin' role"""

        #Create the flavor
        resp, flavor = self.admin_client.create_flavor(self.flavor_name,
                                                        self.ram, self.vcpus,
                                                        self.disk,
                                                        self.ephemeral,
                                                        self.new_flavor_id,
                                                        self.swap, self.rxtx)
        self.assertEqual(200, resp.status)
        self.assertEqual(flavor['name'], self.flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(int(flavor['id']), self.new_flavor_id)
        self.assertEqual(flavor['swap'], self.swap)
        self.assertEqual(flavor['rxtx_factor'], self.rxtx)
        self.assertEqual(flavor['OS-FLV-EXT-DATA:ephemeral'], self.ephemeral)

        #Verify flavor is retrieved
        resp, flavor = self.admin_client.get_flavor_details(self.new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], self.flavor_name)

        #Delete the flavor
        resp, body = self.admin_client.delete_flavor(flavor['id'])
        self.assertEqual(resp.status, 202)

    @attr(type='positive')
    def test_create_flavor_verify_entry_in_list_details(self):
        """Create a flavor and ensure it's details are listed
        This operation requires the user to have 'admin' role"""

        #Create the flavor
        resp, flavor = self.admin_client.create_flavor(self.flavor_name,
                                                        self.ram, self.vcpus,
                                                        self.disk,
                                                        self.ephemeral,
                                                        self.new_flavor_id,
                                                        self.swap, self.rxtx)
        flag = False
        #Verify flavor is retrieved
        resp, flavors = self.admin_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == self.flavor_name:
                flag = True
        self.assertTrue(flag)

        #Delete the flavor
        resp, body = self.admin_client.delete_flavor(self.new_flavor_id)
        self.assertEqual(resp.status, 202)

    @attr(type='negative')
    def test_get_flavor_details_for_deleted_flavor(self):
        """Delete a flavor and ensure it is not listed"""

        # Create a test flavor
        resp, flavor = self.admin_client.create_flavor(self.flavor_name,
                                                self.ram,
                                                self.vcpus, self.disk,
                                                self.ephemeral,
                                                self.new_flavor_id,
                                                self.swap, self.rxtx)
        self.assertEquals(200, resp.status)

        # Delete the flavor
        resp, _ = self.admin_client.delete_flavor(self.new_flavor_id)
        self.assertEqual(resp.status, 202)

        # Get deleted flavor details
        self.assertRaises(exceptions.NotFound,
                self.admin_client.get_flavor_details, self.new_flavor_id)
