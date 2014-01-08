# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


class FlavorsAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminNegativeTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('FlavorExtraData', 'compute'):
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        cls.client = cls.os_adm.flavors_client
        cls.user_client = cls.os.flavors_client
        cls.flavor_name_prefix = 'test_flavor_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.swap = 1024
        cls.rxtx = 2

    def flavor_clean_up(self, flavor_id):
        resp, body = self.client.delete_flavor(flavor_id)
        self.assertEqual(resp.status, 202)
        self.client.wait_for_resource_deletion(flavor_id)

    @test.attr(type=['negative', 'gate'])
    def test_get_flavor_details_for_deleted_flavor(self):
        # Delete a flavor and ensure it is not listed
        # Create a test flavor
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)

        # no need to specify flavor_id, we can get the flavor_id from a
        # response of create_flavor() call.
        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram,
                                                 self.vcpus, self.disk,
                                                 '',
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)
        # Delete the flavor
        new_flavor_id = flavor['id']
        resp_delete, body = self.client.delete_flavor(new_flavor_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(202, resp_delete.status)

        # Deleted flavors can be seen via detailed GET
        resp, flavor = self.client.get_flavor_details(new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(flavor['name'], flavor_name)

        # Deleted flavors should not show up in a list however
        resp, flavors = self.client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        flag = True
        for flavor in flavors:
            if flavor['name'] == flavor_name:
                flag = False
        self.assertTrue(flag)

    @test.attr(type=['negative', 'gate'])
    def test_invalid_is_public_string(self):
        # the 'is_public' parameter can be 'none/true/false' if it exists
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_flavors_with_detail,
                          {'is_public': 'invalid'})

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_as_user(self):
        # only admin user can create a flavor
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.create_flavor,
                          flavor_name, self.ram, self.vcpus, self.disk,
                          new_flavor_id, ephemeral=self.ephemeral,
                          swap=self.swap, rxtx=self.rxtx)

    @test.attr(type=['negative', 'gate'])
    def test_delete_flavor_as_user(self):
        # only admin user can delete a flavor
        self.assertRaises(exceptions.Unauthorized,
                          self.user_client.delete_flavor,
                          self.flavor_ref_alt)

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_using_invalid_ram(self):
        # the 'ram' attribute must be positive integer
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          flavor_name, -1, self.vcpus,
                          self.disk, new_flavor_id)

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_using_invalid_vcpus(self):
        # the 'vcpu' attribute must be positive integer
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          flavor_name, self.ram, -1,
                          self.disk, new_flavor_id)

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_name_length_less_than_1(self):
        # ensure name length >= 1
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          '',
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_name_length_exceeds_255(self):
        # ensure name do not exceed 255 characters
        new_flavor_name = 'a' * 256
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_name(self):
        # the regex of flavor_name is '^[\w\.\- ]*$'
        invalid_flavor_name = data_utils.rand_name('invalid-!@#$%-')
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          invalid_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_flavor_id(self):
        # the regex of flavor_id is '^[\w\.\- ]*$', and it cannot contain
        # leading and/or trailing whitespace
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        invalid_flavor_id = '!@#$%'

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          invalid_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_id_length_exceeds_255(self):
        # the length of flavor_id should not exceed 255 characters
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        invalid_flavor_id = 'a' * 256

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          invalid_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_root_gb(self):
        # root_gb attribute should be non-negative ( >= 0) integer
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          -1,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_ephemeral_gb(self):
        # ephemeral_gb attribute should be non-negative ( >= 0) integer
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=-1,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_swap(self):
        # swap attribute should be non-negative ( >= 0) integer
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=-1,
                          rxtx=self.rxtx,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_rxtx_factor(self):
        # rxtx_factor attribute should be a positive float
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=-1.5,
                          is_public='False')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_with_invalid_is_public(self):
        # is_public attribute should be boolean
        new_flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_flavor,
                          new_flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx,
                          is_public='Invalid')

    @test.attr(type=['negative', 'gate'])
    def test_create_flavor_already_exists(self):
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = str(uuid.uuid4())

        resp, flavor = self.client.create_flavor(flavor_name,
                                                 self.ram, self.vcpus,
                                                 self.disk,
                                                 new_flavor_id,
                                                 ephemeral=self.ephemeral,
                                                 swap=self.swap,
                                                 rxtx=self.rxtx)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.flavor_clean_up, flavor['id'])

        self.assertRaises(exceptions.Conflict,
                          self.client.create_flavor,
                          flavor_name,
                          self.ram, self.vcpus,
                          self.disk,
                          new_flavor_id,
                          ephemeral=self.ephemeral,
                          swap=self.swap,
                          rxtx=self.rxtx)

    @test.attr(type=['negative', 'gate'])
    def test_delete_nonexistent_flavor(self):
        nonexistent_flavor_id = str(uuid.uuid4())

        self.assertRaises(exceptions.NotFound,
                          self.client.delete_flavor,
                          nonexistent_flavor_id)


class FlavorsAdminNegativeTestXML(FlavorsAdminNegativeTestJSON):
    _interface = 'xml'
