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

from tempest.api.compute import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class FlavorsExtraSpecsTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Flavor Extra Spec API extension.

    SET, UNSET, UPDATE Flavor Extra specs require admin privileges.
    GET Flavor Extra specs can be performed even by without admin privileges.
    """

    @classmethod
    def resource_setup(cls):
        super(FlavorsExtraSpecsTestJSON, cls).resource_setup()
        flavor_name = data_utils.rand_name('test_flavor')
        ram = 512
        vcpus = 1
        disk = 10
        ephemeral = 10
        new_flavor_id = data_utils.rand_int_id(start=1000)
        swap = 1024
        rxtx = 1
        # Create a flavor so as to set/get/unset extra specs
        cls.flavor = cls.admin_flavors_client.create_flavor(
            name=flavor_name,
            ram=ram, vcpus=vcpus,
            disk=disk,
            id=new_flavor_id,
            ephemeral=ephemeral,
            swap=swap,
            rxtx_factor=rxtx)['flavor']
        cls.addClassResourceCleanup(
            cls.admin_flavors_client.wait_for_resource_deletion,
            cls.flavor['id'])
        cls.addClassResourceCleanup(cls.admin_flavors_client.delete_flavor,
                                    cls.flavor['id'])

    @decorators.idempotent_id('0b2f9d4b-1ca2-4b99-bb40-165d4bb94208')
    def test_flavor_set_get_update_show_unset_keys(self):
        """Test flavor extra spec operations by admin user

        Test to SET, GET, UPDATE, SHOW, UNSET flavor extra
        spec as a user with admin privileges.
        """
        # Assigning extra specs values that are to be set
        specs = {'hw:numa_nodes': '1', 'hw:cpu_policy': 'shared'}
        # SET extra specs to the flavor created in setUp
        set_body = self.admin_flavors_client.set_flavor_extra_spec(
            self.flavor['id'], **specs)['extra_specs']
        self.assertEqual(set_body, specs)
        # GET extra specs and verify
        get_body = (self.admin_flavors_client.list_flavor_extra_specs(
            self.flavor['id'])['extra_specs'])
        self.assertEqual(get_body, specs)

        # UPDATE the value of the extra specs 'hw:numa_nodes'
        update_body = self.admin_flavors_client.update_flavor_extra_spec(
            self.flavor['id'], "hw:numa_nodes", **{'hw:numa_nodes': '2'})
        self.assertEqual({'hw:numa_nodes': '2'}, update_body)

        # GET extra specs and verify the value of the 'hw:cpu_policy'
        # is the same as before
        get_body = self.admin_flavors_client.list_flavor_extra_specs(
            self.flavor['id'])['extra_specs']
        self.assertEqual(
            get_body, {'hw:numa_nodes': '2', 'hw:cpu_policy': 'shared'}
        )

        # UNSET extra specs that were set in this test
        self.admin_flavors_client.unset_flavor_extra_spec(
            self.flavor['id'], 'hw:numa_nodes'
        )
        self.admin_flavors_client.unset_flavor_extra_spec(
            self.flavor['id'], 'hw:cpu_policy'
        )
        get_body = self.admin_flavors_client.list_flavor_extra_specs(
            self.flavor['id'])['extra_specs']
        self.assertEmpty(get_body)

    @decorators.idempotent_id('a99dad88-ae1c-4fba-aeb4-32f898218bd0')
    def test_flavor_non_admin_get_all_keys(self):
        """Test non admin user getting all flavor extra spec keys"""
        specs = {'hw:numa_nodes': '1', 'hw:cpu_policy': 'shared'}
        self.admin_flavors_client.set_flavor_extra_spec(self.flavor['id'],
                                                        **specs)
        body = (self.flavors_client.list_flavor_extra_specs(
            self.flavor['id'])['extra_specs'])

        for key in specs:
            self.assertEqual(body[key], specs[key])

    @decorators.idempotent_id('12805a7f-39a3-4042-b989-701d5cad9c90')
    def test_flavor_non_admin_get_specific_key(self):
        """Test non admin user getting specific flavor extra spec key"""
        specs = {'hw:numa_nodes': '1', 'hw:cpu_policy': 'shared'}
        body = self.admin_flavors_client.set_flavor_extra_spec(
            self.flavor['id'], **specs
        )['extra_specs']
        self.assertEqual(body['hw:numa_nodes'], '1')
        self.assertIn('hw:cpu_policy', body)

        body = self.flavors_client.show_flavor_extra_spec(
            self.flavor['id'], 'hw:numa_nodes')
        self.assertEqual(body['hw:numa_nodes'], '1')
        self.assertNotIn('hw:cpu_policy', body)


class FlavorMetadataValidation(base.BaseV2ComputeAdminTest):

    min_microversion = '2.86'

    @classmethod
    def resource_setup(cls):
        super(FlavorMetadataValidation, cls).resource_setup()
        cls.flavor_name_prefix = 'test_flavor_validate_metadata_'
        cls.ram = 512
        cls.vcpus = 1
        cls.disk = 10
        cls.ephemeral = 10
        cls.swap = 1024
        cls.rxtx = 2

    @decorators.idempotent_id('d3114f03-b0f2-4dc7-be11-70c0abc178b3')
    def test_flavor_update_with_custom_namespace(self):
        """Test flavor creation with a custom namespace, key and value"""
        flavor_name = data_utils.rand_name(self.flavor_name_prefix)
        flavor_id = self.create_flavor(ram=self.ram,
                                       vcpus=self.vcpus,
                                       disk=self.disk,
                                       name=flavor_name)['id']
        specs = {'hw:cpu_policy': 'shared', 'foo:bar': 'baz'}
        body = self.admin_flavors_client.set_flavor_extra_spec(
            flavor_id,
            **specs)['extra_specs']
        self.assertEqual(body['foo:bar'], 'baz')
        self.assertEqual(body['hw:cpu_policy'], 'shared')
