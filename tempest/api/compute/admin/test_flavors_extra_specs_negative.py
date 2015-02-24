# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright 2013 IBM Corp.
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class FlavorsExtraSpecsNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Negative Tests Flavor Extra Spec API extension.
    SET, UNSET, UPDATE Flavor Extra specs require admin privileges.
    """

    @classmethod
    def skip_checks(cls):
        super(FlavorsExtraSpecsNegativeTestJSON, cls).skip_checks()
        if not test.is_extension_enabled('OS-FLV-EXT-DATA', 'compute'):
            msg = "OS-FLV-EXT-DATA extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FlavorsExtraSpecsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.flavors_client

    @classmethod
    def resource_setup(cls):
        super(FlavorsExtraSpecsNegativeTestJSON, cls).resource_setup()

        flavor_name = data_utils.rand_name('test_flavor')
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = data_utils.rand_int_id(start=1000)
        swap = 1024
        rxtx = 1
        # Create a flavor
        cls.flavor = cls.client.create_flavor(flavor_name,
                                              ram, vcpus,
                                              disk,
                                              cls.new_flavor_id,
                                              ephemeral=ephemeral,
                                              swap=swap, rxtx=rxtx)

    @classmethod
    def resource_cleanup(cls):
        cls.client.delete_flavor(cls.flavor['id'])
        cls.client.wait_for_resource_deletion(cls.flavor['id'])
        super(FlavorsExtraSpecsNegativeTestJSON, cls).resource_cleanup()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a00a3b81-5641-45a8-ab2b-4a8ec41e1d7d')
    def test_flavor_non_admin_set_keys(self):
        # Test to SET flavor extra spec as a user without admin privileges.
        specs = {"key1": "value1", "key2": "value2"}
        self.assertRaises(lib_exc.Forbidden,
                          self.flavors_client.set_flavor_extra_spec,
                          self.flavor['id'],
                          specs)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('1ebf4ef8-759e-48fe-a801-d451d80476fb')
    def test_flavor_non_admin_update_specific_key(self):
        # non admin user is not allowed to update flavor extra spec
        specs = {"key1": "value1", "key2": "value2"}
        body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)
        self.assertEqual(body['key1'], 'value1')
        self.assertRaises(lib_exc.Forbidden,
                          self.flavors_client.
                          update_flavor_extra_spec,
                          self.flavor['id'],
                          'key1',
                          key1='value1_new')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('28f12249-27c7-44c1-8810-1f382f316b11')
    def test_flavor_non_admin_unset_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        self.client.set_flavor_extra_spec(self.flavor['id'], specs)

        self.assertRaises(lib_exc.Forbidden,
                          self.flavors_client.unset_flavor_extra_spec,
                          self.flavor['id'],
                          'key1')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('440b9f3f-3c7f-4293-a106-0ceda350f8de')
    def test_flavor_unset_nonexistent_key(self):
        nonexistent_key = data_utils.rand_name('flavor_key')
        self.assertRaises(lib_exc.NotFound,
                          self.client.unset_flavor_extra_spec,
                          self.flavor['id'],
                          nonexistent_key)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('329a7be3-54b2-48be-8052-bf2ce4afd898')
    def test_flavor_get_nonexistent_key(self):
        self.assertRaises(lib_exc.NotFound,
                          self.flavors_client.get_flavor_extra_spec_with_key,
                          self.flavor['id'],
                          "nonexistent_key")

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('25b822b8-9f49-44f6-80de-d99f0482e5cb')
    def test_flavor_update_mismatch_key(self):
        # the key will be updated should be match the key in the body
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_flavor_extra_spec,
                          self.flavor['id'],
                          "key2",
                          key1="value")

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f5889590-bf66-41cc-b4b1-6e6370cfd93f')
    def test_flavor_update_more_key(self):
        # there should be just one item in the request body
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_flavor_extra_spec,
                          self.flavor['id'],
                          "key1",
                          key1="value",
                          key2="value")
