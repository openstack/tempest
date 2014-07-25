# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class FlavorsAdminV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminV3Test, cls).setUpClass()

        cls.client = cls.flavors_admin_client
        cls.user_client = cls.flavors_client
        cls.flavor_name_prefix = 'test_flavor_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.swap = 1024
        cls.rxtx = 2

    def flavor_clean_up(self, flavor_id):
        resp, body = self.client.delete_flavor(flavor_id)
        self.assertEqual(resp.status, 204)
        self.client.wait_for_resource_deletion(flavor_id)

    def _create_flavor(self, flavor_id):
        # Create a flavor and ensure it is listed
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 flavor_id,
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(201, resp.status)
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(flavor['swap'], self.swap)
        if test.is_extension_enabled("os-flavor-rxtx", "compute_v3"):
            self.assertEqual(flavor['os-flavor-rxtx:rxtx_factor'], self.rxtx)
        self.assertEqual(flavor['ephemeral'],
                         self.ephemeral)
        self.assertEqual(flavor['flavor-access:is_public'], True)

        # Verify flavor is retrieved
        resp, flavor = self.client.get_flavor_details(flavor['id'])
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], flavor_name)

        return flavor['id']

    @test.attr(type='gate')
    def test_create_flavor_with_int_id(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, str(flavor_id))

    @test.attr(type='gate')
    def test_create_flavor_with_uuid_id(self):
        flavor_id = str(uuid.uuid4())
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, flavor_id)

    @test.attr(type='gate')
    def test_create_flavor_with_none_id(self):
        # If nova receives a request with None as flavor_id,
        # nova generates flavor_id of uuid.
        flavor_id = None
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, str(uuid.UUID(new_flavor_id)))

    @test.attr(type='gate')
    def test_create_flavor_verify_entry_in_list_details(self):
        # Create a flavor and ensure it's details are listed
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        flag = False
        # Verify flavor is retrieved
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    def test_create_list_flavor_without_extra_data(self):
        # Create a flavor and ensure it is listed
        # This operation requires the user to have 'admin' role

        def verify_flavor_response_extension(flavor):
            # check some extensions for the flavor create/show/detail response
            self.assertEqual(flavor['swap'], 0)
            if test.is_extension_enabled("os-flavor-rxtx", "compute_v3"):
                self.assertEqual(int(flavor['os-flavor-rxtx:rxtx_factor']), 1)
            self.assertEqual(int(flavor['ephemeral']), 0)
            self.assertEqual(flavor['flavor-access:is_public'], True)

        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(201, resp.status)
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(int(flavor['id']), new_flavor_id)
        verify_flavor_response_extension(flavor)

        # Verify flavor is retrieved
        resp, flavor = self.client.get_flavor_details(new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], flavor_name)
        verify_flavor_response_extension(flavor)

        # Check if flavor is present in list
        resp, flavors = self.user_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                verify_flavor_response_extension(flavor)
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    def test_list_non_public_flavor(self):
        # Create a flavor with os-flavor-access:is_public false should
        # be present in list_details.
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        # Verify flavor is retrieved
        flag = False
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertTrue(flag)

        # Verify flavor is not retrieved with other user
        flag = False
        resp, flavors = self.user_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertFalse(flag)

    @test.attr(type='gate')
    def test_create_server_with_non_public_flavor(self):
        # Create a flavor with os-flavor-access:is_public false
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(201, resp.status)

        # Verify flavor is not used by other user
        self.assertRaises(exceptions.BadRequest,
                          self.servers_client.create_server,
                          'test', self.image_ref, flavor['id'])

    @test.attr(type='gate')
    def test_list_public_flavor_with_other_user(self):
        # Create a Flavor with public access.
        # Try to List/Get flavor with another user
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 is_public="True")
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        flag = False
        self.new_client = self.flavors_client
        # Verify flavor is retrieved with new user
        resp, flavors = self.new_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    def test_is_public_string_variations(self):
        flavor_id_not_public = data_utils.rand_int_id(start=1000)
        flavor_name_not_public = data_utils.rand_name(self.flavor_name_prefix)
        flavor_id_public = data_utils.rand_int_id(start=1000)
        flavor_name_public = data_utils.rand_name(self.flavor_name_prefix)

        # Create a non public flavor
        resp, flavor = self.client.create_flavor(flavor_name_not_public,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 flavor_id_not_public,
                                                 is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])

        # Create a public flavor
        resp, flavor = self.client.create_flavor(flavor_name_public,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 flavor_id_public,
                                                 is_public="True")
        self.addCleanup(self.flavor_clean_up, flavor['id'])

        def _flavor_lookup(flavors, flavor_name):
            for flavor in flavors:
                if flavor['name'] == flavor_name:
                    return flavor
            return None

        def _test_string_variations(variations, flavor_name):
            for string in variations:
                params = {'is_public': string}
                r, flavors = self.client.list_flavors_with_detail(params)
                self.assertEqual(r.status, 200)
                flavor = _flavor_lookup(flavors, flavor_name)
                self.assertIsNotNone(flavor)

        _test_string_variations(['f', 'false', 'no', '0'],
                                flavor_name_not_public)

        _test_string_variations(['t', 'true', 'yes', '1'],
                                flavor_name_public)

    @test.attr(type='gate')
    def test_create_flavor_using_string_ram(self):
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        ram = "1024"
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(201, resp.status)
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], int(ram))
        self.assertEqual(int(flavor['id']), new_flavor_id)
