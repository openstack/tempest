# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation.
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

from tempest.api import compute
from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_int_id
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class FlavorsAccessTestJSON(base.BaseComputeAdminTest):

    """
    Tests Flavor Access API extension.
    Add and remove Flavor Access require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsAccessTestJSON, cls).setUpClass()
        if not compute.FLAVOR_EXTRA_DATA_ENABLED:
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        cls.client = cls.os_adm.flavors_client
        admin_client = cls._get_identity_admin_client()
        resp, tenants = admin_client.list_tenants()
        cls.tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                         cls.flavors_client.tenant_name][0]

        cls.flavor_name_prefix = 'test_flavor_access_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10

    @attr(type='gate')
    def test_flavor_access_add_remove(self):
        # Test to add and remove flavor access to a given tenant.
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        # Add flavor access to a tenant.
        resp_body = {
            "tenant_id": str(self.tenant_id),
            "flavor_id": str(new_flavor['id']),
        }
        add_resp, add_body = \
            self.client.add_flavor_access(new_flavor['id'], self.tenant_id)
        self.assertEqual(add_resp.status, 200)
        self.assertIn(resp_body, add_body)

        # The flavor is present in list.
        resp, flavors = self.flavors_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        self.assertIn(new_flavor['id'], map(lambda x: x['id'], flavors))

        # Remove flavor access from a tenant.
        remove_resp, remove_body = \
            self.client.remove_flavor_access(new_flavor['id'], self.tenant_id)
        self.assertEqual(remove_resp.status, 200)
        self.assertNotIn(resp_body, remove_body)

        # The flavor is not present in list.
        resp, flavors = self.flavors_client.list_flavors_with_detail()
        self.assertEqual(resp.status, 200)
        self.assertNotIn(new_flavor['id'], map(lambda x: x['id'], flavors))

    @attr(type=['negative', 'gate'])
    def test_flavor_non_admin_add(self):
        # Test to add flavor access as a user without admin privileges.
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.add_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @attr(type=['negative', 'gate'])
    def test_flavor_non_admin_remove(self):
        # Test to remove flavor access as a user without admin privileges.
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        # Add flavor access to a tenant.
        self.client.add_flavor_access(new_flavor['id'], self.tenant_id)
        self.addCleanup(self.client.remove_flavor_access,
                        new_flavor['id'], self.tenant_id)
        self.assertRaises(exceptions.Unauthorized,
                          self.flavors_client.remove_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @attr(type=['negative', 'gate'])
    def test_add_flavor_access_duplicate(self):
        # Create a new flavor.
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])

        # Add flavor access to a tenant.
        self.client.add_flavor_access(new_flavor['id'], self.tenant_id)
        self.addCleanup(self.client.remove_flavor_access,
                        new_flavor['id'], self.tenant_id)

        # An exception should be raised when adding flavor access to the same
        # tenant
        self.assertRaises(exceptions.Conflict,
                          self.client.add_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @attr(type=['negative', 'gate'])
    def test_remove_flavor_access_not_found(self):
        # Create a new flavor.
        flavor_name = rand_name(self.flavor_name_prefix)
        new_flavor_id = rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])

        # An exception should be raised when flavor access is not found
        self.assertRaises(exceptions.NotFound,
                          self.client.remove_flavor_access,
                          new_flavor['id'],
                          str(uuid.uuid4()))


class FlavorsAdminTestXML(FlavorsAccessTestJSON):
    _interface = 'xml'
