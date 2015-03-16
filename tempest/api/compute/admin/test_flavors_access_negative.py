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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class FlavorsAccessNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavor Access API extension.
    Add and remove Flavor Access require admin privileges.
    """

    @classmethod
    def skip_checks(cls):
        super(FlavorsAccessNegativeTestJSON, cls).skip_checks()
        if not test.is_extension_enabled('OS-FLV-EXT-DATA', 'compute'):
            msg = "OS-FLV-EXT-DATA extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(FlavorsAccessNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.flavors_client

    @classmethod
    def resource_setup(cls):
        super(FlavorsAccessNegativeTestJSON, cls).resource_setup()

        cls.tenant_id = cls.flavors_client.tenant_id
        cls.flavor_name_prefix = 'test_flavor_access_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0621c53e-d45d-40e7-951d-43e5e257b272')
    def test_flavor_access_list_with_public_flavor(self):
        # Test to list flavor access with exceptions by querying public flavor
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor = self.client.create_flavor(flavor_name,
                                               self.ram, self.vcpus,
                                               self.disk,
                                               new_flavor_id,
                                               is_public='True')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        self.assertRaises(lib_exc.NotFound,
                          self.client.list_flavor_access,
                          new_flavor_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('41eaaade-6d37-4f28-9c74-f21b46ca67bd')
    def test_flavor_non_admin_add(self):
        # Test to add flavor access as a user without admin privileges.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor = self.client.create_flavor(flavor_name,
                                               self.ram, self.vcpus,
                                               self.disk,
                                               new_flavor_id,
                                               is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        self.assertRaises(lib_exc.Forbidden,
                          self.flavors_client.add_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('073e79a6-c311-4525-82dc-6083d919cb3a')
    def test_flavor_non_admin_remove(self):
        # Test to remove flavor access as a user without admin privileges.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor = self.client.create_flavor(flavor_name,
                                               self.ram, self.vcpus,
                                               self.disk,
                                               new_flavor_id,
                                               is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        # Add flavor access to a tenant.
        self.client.add_flavor_access(new_flavor['id'], self.tenant_id)
        self.addCleanup(self.client.remove_flavor_access,
                        new_flavor['id'], self.tenant_id)
        self.assertRaises(lib_exc.Forbidden,
                          self.flavors_client.remove_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f3592cc0-0306-483c-b210-9a7b5346eddc')
    def test_add_flavor_access_duplicate(self):
        # Create a new flavor.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor = self.client.create_flavor(flavor_name,
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
        self.assertRaises(lib_exc.Conflict,
                          self.client.add_flavor_access,
                          new_flavor['id'],
                          self.tenant_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('1f710927-3bc7-4381-9f82-0ca6e42644b7')
    def test_remove_flavor_access_not_found(self):
        # Create a new flavor.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        new_flavor = self.client.create_flavor(flavor_name,
                                               self.ram, self.vcpus,
                                               self.disk,
                                               new_flavor_id,
                                               is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])

        # An exception should be raised when flavor access is not found
        self.assertRaises(lib_exc.NotFound,
                          self.client.remove_flavor_access,
                          new_flavor['id'],
                          str(uuid.uuid4()))
