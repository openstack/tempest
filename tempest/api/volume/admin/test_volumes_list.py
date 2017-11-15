# Copyright 2016 Red Hat, Inc.
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
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumesListAdminTestJSON(base.BaseVolumeAdminTest):

    @classmethod
    def resource_setup(cls):
        super(VolumesListAdminTestJSON, cls).resource_setup()
        # Create 3 test volumes
        # NOTE(zhufl): When using pre-provisioned credentials, the project
        # may have volumes other than those created below.
        cls.volume_list = cls.volumes_client.list_volumes()['volumes']
        for _ in range(3):
            volume = cls.create_volume()
            # Fetch volume details
            volume_details = cls.volumes_client.show_volume(
                volume['id'])['volume']
            cls.volume_list.append(volume_details)

    @decorators.idempotent_id('5866286f-3290-4cfd-a414-088aa6cdc469')
    def test_volume_list_param_tenant(self):
        # Test to list volumes from single tenant
        # Create a volume in admin tenant
        adm_vol = self.admin_volume_client.create_volume(
            size=CONF.volume.volume_size)['volume']
        self.addCleanup(self.admin_volume_client.delete_volume, adm_vol['id'])
        waiters.wait_for_volume_resource_status(self.admin_volume_client,
                                                adm_vol['id'], 'available')
        params = {'all_tenants': 1,
                  'project_id': self.volumes_client.tenant_id}
        # Getting volume list from primary tenant using admin credentials
        fetched_list = self.admin_volume_client.list_volumes(
            detail=True, params=params)['volumes']
        # Verifying fetched volume ids list is related to primary tenant
        fetched_list_ids = map(operator.itemgetter('id'), fetched_list)
        expected_list_ids = map(operator.itemgetter('id'), self.volume_list)
        self.assertEqual(sorted(expected_list_ids), sorted(fetched_list_ids))
        # Verifying tenant id of volumes fetched list is related to
        # primary tenant
        fetched_tenant_id = [operator.itemgetter(
            'os-vol-tenant-attr:tenant_id')(item) for item in fetched_list]
        expected_tenant_id = [self.volumes_client.tenant_id] * \
            len(self.volume_list)
        self.assertEqual(expected_tenant_id, fetched_tenant_id)
