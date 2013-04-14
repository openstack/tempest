# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest import exceptions
from tempest.test import attr
from tempest.tests import compute
from tempest.tests.compute import base


class FlavorsExtraSpecsTestJSON(base.BaseComputeAdminTest):

    """
    Tests Flavor Extra Spec API extension.
    SET, UNSET Flavor Extra specs require admin privileges.
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
        flavor_name = 'test_flavor2'
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        cls.new_flavor_id = 12345
        swap = 1024
        rxtx = 1
        #Create a flavor so as to set/get/unset extra specs
        resp, cls.flavor = cls.client.create_flavor(flavor_name,
                                                    ram, vcpus,
                                                    disk,
                                                    cls.new_flavor_id,
                                                    ephemeral=ephemeral,
                                                    swap=swap, rxtx=rxtx)

    @classmethod
    def tearDownClass(cls):
        resp, body = cls.client.delete_flavor(cls.flavor['id'])
        super(FlavorsExtraSpecsTestJSON, cls).tearDownClass()

    def test_flavor_set_get_unset_keys(self):
        #Test to SET, GET UNSET flavor extra spec as a user
        #with admin privileges.
        #Assigning extra specs values that are to be set
        specs = {"key1": "value1", "key2": "value2"}
        #SET extra specs to the flavor created in setUp
        set_resp, set_body = \
            self.client.set_flavor_extra_spec(self.flavor['id'], specs)
        self.assertEqual(set_resp.status, 200)
        self.assertEqual(set_body, specs)
        #GET extra specs and verify
        get_resp, get_body = \
            self.client.get_flavor_extra_spec(self.flavor['id'])
        self.assertEqual(get_resp.status, 200)
        self.assertEqual(get_body, specs)
        #UNSET extra specs that were set in this test
        unset_resp, _ = \
            self.client.unset_flavor_extra_spec(self.flavor['id'], "key1")
        self.assertEqual(unset_resp.status, 200)

    @attr('negative')
    def test_flavor_non_admin_set_keys(self):
        #Test to SET flavor extra spec as a user without admin privileges.
        specs = {"key1": "value1", "key2": "value2"}
        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.set_flavor_extra_spec,
                          self.flavor['id'],
                          specs)

    def test_flavor_non_admin_get_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        set_resp, set_body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)
        resp, body = self.flavors_client.get_flavor_extra_spec(
            self.flavor['id'])
        self.assertEqual(resp.status, 200)
        for key in specs:
            self.assertEquals(body[key], specs[key])

    @attr('negative')
    def test_flavor_non_admin_unset_keys(self):
        specs = {"key1": "value1", "key2": "value2"}
        set_resp, set_body = self.client.set_flavor_extra_spec(
            self.flavor['id'], specs)

        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.unset_flavor_extra_spec,
                          self.flavor['id'],
                          'key1')


class FlavorsExtraSpecsTestXML(FlavorsExtraSpecsTestJSON):
    _interface = 'xml'
