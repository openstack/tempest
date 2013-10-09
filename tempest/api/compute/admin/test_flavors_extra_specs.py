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

from tempest.api import compute
from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_int_id
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr


class FlavorsExtraSpecsTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavor Extra Spec API extension.
    SET, UNSET, UPDATE Flavor Extra specs require admin privileges.
    GET Flavor Extra specs can be performed even by without admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsExtraSpecsTestJSON, cls).setUpClass()
        if not compute.FLAVOR_EXTRA_DATA_ENABLED:
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        cls.client = cls.os_adm.flavors_client
        flavor_name = rand_name('test_flavor')
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = rand_int_id(start=1000)
        swap = 1024
        rxtx = 1
        # Create a flavor so as to set/get/unset extra specs
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
        super(FlavorsExtraSpecsTestJSON, cls).tearDownClass()

    @attr(type='gate')
    def test_flavor_set_get_update_show_unset_keys(self):
        # Test to SET, GET, UPDATE, SHOW, UNSET flavor extra
        # spec as a user with admin privileges.
        # Assigning extra specs values that are to be set
        specs = {"key1": "value1", "key2": "value2"}
        # SET extra specs to the flavor created in setUp
        set_resp, set_body = \
            self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        self.assertEqual(set_resp.status, 200)
        self.assertEqual(set_body, specs)
        # GET extra specs and verify
        get_resp, get_body = \
            self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_resp.status, 200)
        self.assertEqual(get_body, specs)

        # UPDATE the value of the extra specs key1
        update_resp, update_body = \
            self.client.update_flavor_extra_spec(self.flavor['id'],
                                                 "key1",
                                                 key1="value")
        self.assertEqual(update_resp.status, 200)
        self.assertEqual({"key1": "value"}, update_body)

        # GET extra specs and verify the value of the key2
        # is the same as before
        get_resp, get_body = \
            self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_resp.status, 200)
        self.assertEqual(get_body, {"key1": "value", "key2": "value2"})

        # UNSET extra specs that were set in this test
        unset_resp, _ = \
            self.client.unset_flavor_extra_spec(self.flavor['id'], "key1")
        self.assertEqual(unset_resp.status, 200)
        unset_resp, _ = \
            self.client.unset_flavor_extra_spec(self.flavor['id'], "key2")
        self.assertEqual(unset_resp.status, 200)

    @attr(type='gate')
    def test_flavor_non_admin_get_all_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        set_resp, set_body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)
        resp, body = self.flavors_client.get_flavor_extra_spec(
            self.flavor['id'])
        self.assertEqual(resp.status, 200)

        for key in specs:
            self.assertEqual(body[key], specs[key])

    @attr(type='gate')
    def test_flavor_non_admin_get_specific_key(self):
        specs = {"key1": "value1", "key2": "value2"}
        resp, body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)
        self.assertEqual(resp.status, 200)
        self.assertEqual(body['key1'], 'value1')
        self.assertIn('key2', body)
        resp, body = self.flavors_client.get_flavor_extra_spec_with_key(
            self.flavor['id'], 'key1')
        self.assertEqual(resp.status, 200)
        self.assertEqual(body['key1'], 'value1')
        self.assertNotIn('key2', body)


class FlavorsExtraSpecsTestXML(FlavorsExtraSpecsTestJSON):
    _interface = 'xml'
