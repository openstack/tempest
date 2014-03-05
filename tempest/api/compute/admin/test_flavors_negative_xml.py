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

from tempest.api.compute.admin import test_flavors_negative
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class FlavorsAdminNegativeTestXML(test_flavors_negative.
                                  FlavorsAdminNegativeTestJSON):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    _interface = 'xml'

    def flavor_clean_up(self, flavor_id):
        resp, body = self.client.delete_flavor(flavor_id)
        self.assertEqual(resp.status, 202)
        self.client.wait_for_resource_deletion(flavor_id)

    @test.attr(type=['negative', 'gate'])
    def test_invalid_is_public_string(self):
        # the 'is_public' parameter can be 'none/true/false' if it exists
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_flavors_with_detail,
                          {'is_public': 'invalid'})

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
