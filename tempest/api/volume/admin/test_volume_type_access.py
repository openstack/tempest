# Copyright 2016 OpenStack Foundation
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

import operator

from tempest.api.volume import base
from tempest.common import waiters
from tempest.lib import exceptions as lib_exc
from tempest import test


class VolumeTypesAccessV2Test(base.BaseVolumeAdminTest):

    credentials = ['primary', 'alt', 'admin']

    @classmethod
    def setup_clients(cls):
        super(VolumeTypesAccessV2Test, cls).setup_clients()
        cls.alt_client = cls.os_alt.volumes_client

    @test.idempotent_id('d4dd0027-835f-4554-a6e5-50903fb79184')
    def test_volume_type_access_add(self):
        # Creating a NON public volume type
        params = {'os-volume-type-access:is_public': False}
        volume_type = self.create_volume_type(**params)

        # Try creating a volume from volume type in primary tenant
        self.assertRaises(lib_exc.NotFound, self.volumes_client.create_volume,
                          volume_type=volume_type['id'])

        # Adding volume type access for primary tenant
        self.admin_volume_types_client.add_type_access(
            volume_type['id'], project=self.volumes_client.tenant_id)
        self.addCleanup(self.admin_volume_types_client.remove_type_access,
                        volume_type['id'],
                        project=self.volumes_client.tenant_id)

        # Creating a volume from primary tenant
        volume = self.volumes_client.create_volume(
            volume_type=volume_type['id'])['volume']
        self.addCleanup(self.delete_volume, self.volumes_client, volume['id'])
        waiters.wait_for_volume_status(self.volumes_client, volume['id'],
                                       'available')

        # Validating the created volume is based on the volume type
        self.assertEqual(volume_type['name'], volume['volume_type'])

    @test.idempotent_id('5220eb28-a435-43ce-baaf-ed46f0e95159')
    def test_volume_type_access_list(self):
        # Creating a NON public volume type
        params = {'os-volume-type-access:is_public': False}
        volume_type = self.create_volume_type(**params)

        # Adding volume type access for primary tenant
        self.admin_volume_types_client.add_type_access(
            volume_type['id'], project=self.volumes_client.tenant_id)
        self.addCleanup(self.admin_volume_types_client.remove_type_access,
                        volume_type['id'],
                        project=self.volumes_client.tenant_id)

        # Adding volume type access for alt tenant
        self.admin_volume_types_client.add_type_access(
            volume_type['id'], project=self.alt_client.tenant_id)
        self.addCleanup(self.admin_volume_types_client.remove_type_access,
                        volume_type['id'],
                        project=self.alt_client.tenant_id)

        # List tenant access for the given volume type
        type_access_list = self.admin_volume_types_client.list_type_access(
            volume_type['id'])['volume_type_access']
        volume_type_ids = [
            vol_type['volume_type_id'] for vol_type in type_access_list
        ]

        # Validating volume type available for only two tenants
        self.assertEqual(2, volume_type_ids.count(volume_type['id']))

        # Validating the permitted tenants are the expected tenants
        self.assertIn(self.volumes_client.tenant_id,
                      map(operator.itemgetter('project_id'), type_access_list))
        self.assertIn(self.alt_client.tenant_id,
                      map(operator.itemgetter('project_id'), type_access_list))
