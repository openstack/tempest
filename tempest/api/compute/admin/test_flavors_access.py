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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import test


class FlavorsAccessTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Flavor Access API extension.
    Add and remove Flavor Access require admin privileges.
    """

    @classmethod
    def setUpClass(cls):
        super(FlavorsAccessTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('FlavorExtraData', 'compute'):
            msg = "FlavorExtraData extension not enabled."
            raise cls.skipException(msg)

        # Compute admin flavor client
        cls.client = cls.os_adm.flavors_client
        # Non admin tenant ID
        cls.tenant_id = cls.flavors_client.tenant_id
        # Compute admin tenant ID
        cls.adm_tenant_id = cls.client.tenant_id
        cls.flavor_name_prefix = 'test_flavor_access_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10

    @test.attr(type='gate')
    def test_flavor_access_list_with_private_flavor(self):
        # Test to make sure that list flavor access on a newly created
        # private flavor will return an empty access list
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
        resp, new_flavor = self.client.create_flavor(flavor_name,
                                                     self.ram, self.vcpus,
                                                     self.disk,
                                                     new_flavor_id,
                                                     is_public='False')
        self.addCleanup(self.client.delete_flavor, new_flavor['id'])
        self.assertEqual(resp.status, 200)
        resp, flavor_access = self.client.list_flavor_access(new_flavor_id)
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(flavor_access), 0, str(flavor_access))

    @test.attr(type='gate')
    def test_flavor_access_add_remove(self):
        # Test to add and remove flavor access to a given tenant.
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        new_flavor_id = data_utils.rand_int_id(start=1000)
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


class FlavorsAdminTestXML(FlavorsAccessTestJSON):
    _interface = 'xml'
