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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class FlavorsAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @classmethod
    def skip_checks(cls):
        super(FlavorsAdminTestJSON, cls).skip_checks()
        if not test.is_extension_enabled('OS-FLV-EXT-DATA', 'compute'):
            msg = "OS-FLV-EXT-DATA extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FlavorsAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.flavors_client
        cls.user_client = cls.os.flavors_client

    @classmethod
    def resource_setup(cls):
        super(FlavorsAdminTestJSON, cls).resource_setup()

        cls.flavor_name_prefix = 'test_flavor_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.swap = 1024
        cls.rxtx = 2

    def flavor_clean_up(self, flavor_id):
        self.client.delete_flavor(flavor_id)
        self.client.wait_for_resource_deletion(flavor_id)

    def _create_flavor(self, flavor_id):
        # Create a flavor and ensure it is listed
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           flavor_id,
                                           ephemeral=self.ephemeral,
                                           swap=self.swap,
                                           rxtx=self.rxtx)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(flavor['swap'], self.swap)
        self.assertEqual(flavor['rxtx_factor'], self.rxtx)
        self.assertEqual(flavor['OS-FLV-EXT-DATA:ephemeral'],
                         self.ephemeral)
        self.assertEqual(flavor['os-flavor-access:is_public'], True)

        # Verify flavor is retrieved
        flavor = self.client.get_flavor_details(flavor['id'])
        self.assertEqual(flavor['name'], flavor_name)

        return flavor['id']

    @test.attr(type='gate')
    @test.idempotent_id('8b4330e1-12c4-4554-9390-e6639971f086')
    def test_create_flavor_with_int_id(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, str(flavor_id))

    @test.attr(type='gate')
    @test.idempotent_id('94c9bb4e-2c2a-4f3c-bb1f-5f0daf918e6d')
    def test_create_flavor_with_uuid_id(self):
        flavor_id = str(uuid.uuid4())
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, flavor_id)

    @test.attr(type='gate')
    @test.idempotent_id('f83fe669-6758-448a-a85e-32d351f36fe0')
    def test_create_flavor_with_none_id(self):
        # If nova receives a request with None as flavor_id,
        # nova generates flavor_id of uuid.
        flavor_id = None
        new_flavor_id = self._create_flavor(flavor_id)
        self.assertEqual(new_flavor_id, str(uuid.UUID(new_flavor_id)))

    @test.attr(type='gate')
    @test.idempotent_id('8261d7b0-be58-43ec-a2e5-300573c3f6c5')
    def test_create_flavor_verify_entry_in_list_details(self):
        # Create a flavor and ensure it's details are listed
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id,
                                           ephemeral=self.ephemeral,
                                           swap=self.swap,
                                           rxtx=self.rxtx)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        flag = False
        # Verify flavor is retrieved
        flavors = self.client.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    @test.idempotent_id('63dc64e6-2e79-4fdf-868f-85500d308d66')
    def test_create_list_flavor_without_extra_data(self):
        # Create a flavor and ensure it is listed
        # This operation requires the user to have 'admin' role

        def verify_flavor_response_extension(flavor):
            # check some extensions for the flavor create/show/detail response
            self.assertEqual(flavor['swap'], '')
            self.assertEqual(int(flavor['rxtx_factor']), 1)
            self.assertEqual(int(flavor['OS-FLV-EXT-DATA:ephemeral']), 0)
            self.assertEqual(flavor['os-flavor-access:is_public'], True)

        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['ram'], self.ram)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(int(flavor['id']), new_flavor_id)
        verify_flavor_response_extension(flavor)

        # Verify flavor is retrieved
        flavor = self.client.get_flavor_details(new_flavor_id)
        self.assertEqual(flavor['name'], flavor_name)
        verify_flavor_response_extension(flavor)

        # Check if flavor is present in list
        flavors = self.user_client.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                verify_flavor_response_extension(flavor)
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    @test.idempotent_id('be6cc18c-7c5d-48c0-ac16-17eaf03c54eb')
    def test_list_non_public_flavor(self):
        # Create a flavor with os-flavor-access:is_public false.
        # The flavor should not be present in list_details as the
        # tenant is not automatically added access list.
        # This operation requires the user to have 'admin' role
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id,
                                           is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        # Verify flavor is retrieved
        flag = False
        flavors = self.client.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertFalse(flag)

        # Verify flavor is not retrieved with other user
        flag = False
        flavors = self.user_client.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertFalse(flag)

    @test.attr(type='gate')
    @test.idempotent_id('bcc418ef-799b-47cc-baa1-ce01368b8987')
    def test_create_server_with_non_public_flavor(self):
        # Create a flavor with os-flavor-access:is_public false
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id,
                                           is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])

        # Verify flavor is not used by other user
        self.assertRaises(lib_exc.BadRequest,
                          self.os.servers_client.create_server,
                          'test', self.image_ref, flavor['id'])

    @test.attr(type='gate')
    @test.idempotent_id('b345b196-bfbd-4231-8ac1-6d7fe15ff3a3')
    def test_list_public_flavor_with_other_user(self):
        # Create a Flavor with public access.
        # Try to List/Get flavor with another user
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        # Create the flavor
        flavor = self.client.create_flavor(flavor_name,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id,
                                           is_public="True")
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        flag = False
        self.new_client = self.flavors_client
        # Verify flavor is retrieved with new user
        flavors = self.new_client.list_flavors_with_detail()
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = True
        self.assertTrue(flag)

    @test.attr(type='gate')
    @test.idempotent_id('fb9cbde6-3a0e-41f2-a983-bdb0a823c44e')
    def test_is_public_string_variations(self):
        flavor_id_not_public = data_utils.rand_int_id(start=1000)
        flavor_name_not_public = data_utils.rand_name(self.flavor_name_prefix)
        flavor_id_public = data_utils.rand_int_id(start=1000)
        flavor_name_public = data_utils.rand_name(self.flavor_name_prefix)

        # Create a non public flavor
        flavor = self.client.create_flavor(flavor_name_not_public,
                                           self.ram, self.vcpus,
                                           self.disk,
                                           flavor_id_not_public,
                                           is_public="False")
        self.addCleanup(self.flavor_clean_up, flavor['id'])

        # Create a public flavor
        flavor = self.client.create_flavor(flavor_name_public,
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
                flavors = self.client.list_flavors_with_detail(params)
                flavor = _flavor_lookup(flavors, flavor_name)
                self.assertIsNotNone(flavor)

        _test_string_variations(['f', 'false', 'no', '0'],
                                flavor_name_not_public)

        _test_string_variations(['t', 'true', 'yes', '1'],
                                flavor_name_public)

    @test.attr(type='gate')
    @test.idempotent_id('3b541a2e-2ac2-4b42-8b8d-ba6e22fcd4da')
    def test_create_flavor_using_string_ram(self):
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)

        ram = "1024"
        flavor = self.client.create_flavor(flavor_name,
                                           ram, self.vcpus,
                                           self.disk,
                                           new_flavor_id)
        self.addCleanup(self.flavor_clean_up, flavor['id'])
        self.assertEqual(flavor['name'], flavor_name)
        self.assertEqual(flavor['vcpus'], self.vcpus)
        self.assertEqual(flavor['disk'], self.disk)
        self.assertEqual(flavor['ram'], int(ram))
        self.assertEqual(int(flavor['id']), new_flavor_id)
