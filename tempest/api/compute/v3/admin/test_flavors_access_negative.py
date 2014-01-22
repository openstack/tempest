# Copyright 2013 IBM Corporation
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


class FlavorsAccessNegativeV3TestJSON(base.BaseV3ComputeAdminTest):

    """
    Tests Flavor Access API extension.
    Add and remove Flavor Access require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FlavorsAccessNegativeV3TestJSON, cls).setUpClass()

        cls.client = cls.flavors_admin_client
        admin_client = cls._get_identity_admin_client()
        cls.tenant = admin_client.get_tenant_by_name(cls.flavors_client.
                                                     tenant_name)
        cls.tenant_id = cls.tenant['id']
        cls.adm_tenant = admin_client.get_tenant_by_name(
            cls.flavors_admin_client.tenant_name)
        cls.adm_tenant_id = cls.adm_tenant['id']
        cls.flavor_name_prefix = 'test_flavor_access_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10

    @test.attr(type=['negative', 'gate'])
    def test_flavor_access_list_with_public_flavor(self):
        # Test to list flavor access with exceptions by querying public flavor
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='True')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        self.assertEqual(resp.status, 201)
        self.assertRaises(exceptions.NotFound,
                          self.client.list_flavor_access,
                          new_flavor_id)

    @test.attr(type=['negative', 'gate'])
    def test_flavor_non_admin_add(self):
        # Test to add flavor access as a user without admin privileges.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
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

    @test.attr(type=['negative', 'gate'])
    def test_flavor_non_admin_remove(self):
        # Test to remove flavor access as a user without admin privileges.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
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

    @test.attr(type=['negative', 'gate'])
    def test_add_flavor_access_duplicate(self):
        # Create a new flavor.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
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

    @test.attr(type=['negative', 'gate'])
    def test_remove_flavor_access_not_found(self):
        # Create a new flavor.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
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


class FlavorsAdminNegativeV3TestXML(FlavorsAccessNegativeV3TestJSON):
    _interface = 'xml'
