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

load_tests = test.NegativeAutoTest.load_tests


class FlavorsAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavors API Create and Delete that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(FlavorsAdminNegativeTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('OS-FLV-EXT-DATA', 'compute'):
            msg = "OS-FLV-EXT-DATA extension not enabled."
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


@test.SimpleNegativeAutoTest
class FlavorCreateNegativeTestJSON(base.BaseV2ComputeAdminTest,
                                   test.NegativeAutoTest):
    _interface = 'json'
    _service = 'compute'
    _schema_file = 'compute/admin/flavor_create.json'
