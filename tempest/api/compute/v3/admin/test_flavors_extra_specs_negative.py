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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class FlavorsExtraSpecsNegativeV3Test(base.BaseV3ComputeAdminTest):

    """
    Negative Tests Flavor Extra Spec API extension.
    SET, UNSET, UPDATE Flavor Extra specs require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsExtraSpecsNegativeV3Test, cls).setUpClass()

        cls.client = cls.flavors_admin_client
        flavor_name = data_utils.rand_name('test_flavor')
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = data_utils.rand_int_id(start=1000)
        swap = 1024
        rxtx = 1
        # Create a flavor
        resp, cls.flavor = cls.client.create_flavor(flavor_name,
                                                    ram, vcpus,
                                                    disk,
                                                    cls.new_flavor_id,
                                                    ephemeral=ephemeral,
                                                    swap=swap, rxtx=rxtx)

    @classmethod
    def tearDownClass(cls):
        resp, body = cls.client.delete_flavor(cls.flavor['id'])
        cls.client.wait_for_resource_deletion(cls.flavor['id'])
        super(FlavorsExtraSpecsNegativeV3Test, cls).tearDownClass()

    @test.attr(type=['negative', 'gate'])
    def test_flavor_non_admin_set_keys(self):
        # Test to SET flavor extra spec as a user without admin privileges.
        specs = {"key1": "value1", "key2": "value2"}
        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.set_flavor_extra_spec,
                          self.flavor['id'],
                          specs)

    @test.attr(type=['negative', 'gate'])
    def test_flavor_non_admin_update_specific_key(self):
        # non admin user is not allowed to update flavor extra spec
        specs = {"key1": "value1", "key2": "value2"}
        resp, body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)
        self.assertEqual(resp.status, 201)
        self.assertEqual(body['key1'], 'value1')
        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.
                          update_flavor_extra_spec,
                          self.flavor['id'],
                          'key1',
                          key1='value1_new')

    @test.attr(type=['negative', 'gate'])
    def test_flavor_non_admin_unset_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        set_resp, set_body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)

        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.unset_flavor_extra_spec,
                          self.flavor['id'],
                          'key1')

    @test.attr(type=['negative', 'gate'])
    def test_flavor_unset_nonexistent_key(self):
        nonexistent_key = data_utils.rand_name('flavor_key')
        self.assertRaises(exceptions.NotFound,
                          self.client.unset_flavor_extra_spec,
                          self.flavor['id'],
                          nonexistent_key)

    @test.attr(type=['negative', 'gate'])
    def test_flavor_get_nonexistent_key(self):
        self.assertRaises(exceptions.NotFound,
                          self.flavors_client.get_flavor_extra_spec_with_key,
                          self.flavor['id'],
                          "nonexistent_key")

    @test.attr(type=['negative', 'gate'])
    def test_flavor_update_mismatch_key(self):
        # the key will be updated should be match the key in the body
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_flavor_extra_spec,
                          self.flavor['id'],
                          "key2",
                          key1="value")

    @test.attr(type=['negative', 'gate'])
    def test_flavor_update_more_key(self):
        # there should be just one item in the request body
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_flavor_extra_spec,
                          self.flavor['id'],
                          "key1",
                          key1="value",
                          key2="value")
