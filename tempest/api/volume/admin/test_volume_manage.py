# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from tempest.api.volume import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class VolumeManageAdminTest(base.BaseVolumeAdminTest):
    """Test volume manage by admin users"""

    @classmethod
    def skip_checks(cls):
        super(VolumeManageAdminTest, cls).skip_checks()

        if not CONF.volume_feature_enabled.manage_volume:
            raise cls.skipException("Manage volume tests are disabled")

        if len(CONF.volume.manage_volume_ref) != 2:
            msg = ("Manage volume ref is not correctly configured, "
                   "it should be a list of two elements")
            raise exceptions.InvalidConfiguration(msg)

    @decorators.idempotent_id('70076c71-0ce1-4208-a8ff-36a66e65cc1e')
    def test_unmanage_manage_volume(self):
        """Test unmanaging and managing volume"""
        # Create original volume
        org_vol_id = self.create_volume()['id']
        org_vol_info = self.admin_volume_client.show_volume(
            org_vol_id)['volume']

        # Unmanage the original volume
        self.admin_volume_client.unmanage_volume(org_vol_id)
        self.admin_volume_client.wait_for_resource_deletion(org_vol_id)

        # Verify the original volume does not exist in volume list
        params = {'all_tenants': 1}
        all_tenants_volumes = self.admin_volume_client.list_volumes(
            detail=True, params=params)['volumes']
        self.assertNotIn(org_vol_id, [v['id'] for v in all_tenants_volumes])

        # Manage volume
        new_vol_name = data_utils.rand_name(
            self.__class__.__name__ + '-volume')
        new_vol_ref = {
            'name': new_vol_name,
            'host': org_vol_info['os-vol-host-attr:host'],
            'ref': {CONF.volume.manage_volume_ref[0]:
                    CONF.volume.manage_volume_ref[1] % org_vol_id},
            'volume_type': org_vol_info['volume_type'],
            'availability_zone': org_vol_info['availability_zone']}
        new_vol_id = self.admin_volume_manage_client.manage_volume(
            **new_vol_ref)['volume']['id']
        self.addCleanup(self.delete_volume,
                        self.admin_volume_client, new_vol_id)
        waiters.wait_for_volume_resource_status(self.admin_volume_client,
                                                new_vol_id, 'available')

        # Compare the managed volume with the original
        new_vol_info = self.admin_volume_client.show_volume(
            new_vol_id)['volume']
        self.assertNotIn(new_vol_id, [org_vol_id])
        self.assertEqual(new_vol_info['name'], new_vol_name)
        for key in ['size',
                    'volume_type',
                    'availability_zone',
                    'os-vol-host-attr:host']:
            self.assertEqual(new_vol_info[key], org_vol_info[key])
