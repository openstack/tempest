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

from tempest_lib.common.utils import data_utils

from tempest.api.compute import base
from tempest import test


class FlavorsExtraSpecsTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavor Extra Spec API extension.
    SET, UNSET, UPDATE Flavor Extra specs require admin privileges.
    GET Flavor Extra specs can be performed even by without admin privileges.
    """

    @classmethod
    def skip_checks(cls):
        super(FlavorsExtraSpecsTestJSON, cls).skip_checks()
        if not test.is_extension_enabled('OS-FLV-EXT-DATA', 'compute'):
            msg = "OS-FLV-EXT-DATA extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FlavorsExtraSpecsTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.flavors_client

    @classmethod
    def resource_setup(cls):
        super(FlavorsExtraSpecsTestJSON, cls).resource_setup()
        flavor_name = data_utils.rand_name('test_flavor')
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = data_utils.rand_int_id(start=1000)
        swap = 1024
        rxtx = 1
        # Create a flavor so as to set/get/unset extra specs
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
        super(FlavorsExtraSpecsTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    @test.idempotent_id('0b2f9d4b-1ca2-4b99-bb40-165d4bb94208')
    def test_flavor_set_get_update_show_unset_keys(self):
        # Test to SET, GET, UPDATE, SHOW, UNSET flavor extra
        # spec as a user with admin privileges.
        # Assigning extra specs values that are to be set
        specs = {"key1": "value1", "key2": "value2"}
        # SET extra specs to the flavor created in setUp
        set_body = \
            self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        self.assertEqual(set_body, specs)
        # GET extra specs and verify
        get_body = self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_body, specs)

        # UPDATE the value of the extra specs key1
        update_body = \
            self.client.update_flavor_extra_spec(self.flavor['id'],
                                                 "key1",
                                                 key1="value")
        self.assertEqual({"key1": "value"}, update_body)

        # GET extra specs and verify the value of the key2
        # is the same as before
        get_body = self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_body, {"key1": "value", "key2": "value2"})

        # UNSET extra specs that were set in this test
        self.client.unset_flavor_extra_spec(self.flavor['id'], "key1")
        self.client.unset_flavor_extra_spec(self.flavor['id'], "key2")

    @test.attr(type='gate')
    @test.idempotent_id('a99dad88-ae1c-4fba-aeb4-32f898218bd0')
    def test_flavor_non_admin_get_all_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        body = self.flavors_client.get_flavor_extra_spec(self.flavor['id'])

        for key in specs:
            self.assertEqual(body[key], specs[key])

    @test.attr(type='gate')
    @test.idempotent_id('12805a7f-39a3-4042-b989-701d5cad9c90')
    def test_flavor_non_admin_get_specific_key(self):
        specs = {"key1": "value1", "key2": "value2"}
        body = self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        self.assertEqual(body['key1'], 'value1')
        self.assertIn('key2', body)
        body = self.flavors_client.get_flavor_extra_spec_with_key(
            self.flavor['id'], 'key1')
        self.assertEqual(body['key1'], 'value1')
        self.assertNotIn('key2', body)
