# Copyright 2014 OpenStack Foundation
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
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes', 'backups',
              'backup_gigabytes', 'per_volume_gigabytes']


class VolumeQuotasNegativeTestJSON(base.BaseVolumeAdminTest):

    @classmethod
    def setup_credentials(cls):
        super(VolumeQuotasNegativeTestJSON, cls).setup_credentials()
        cls.demo_tenant_id = cls.os_primary.credentials.tenant_id

    @classmethod
    def resource_setup(cls):
        super(VolumeQuotasNegativeTestJSON, cls).resource_setup()

        # Save the current set of quotas, then set up the cleanup method
        # to restore the quotas to their original values after the tests
        # from this class are done. This is needed just in case Tempest is
        # configured to use pre-provisioned projects/user accounts.
        original_quota_set = (cls.admin_quotas_client.show_quota_set(
            cls.demo_tenant_id)['quota_set'])
        cleanup_quota_set = dict(
            (k, v) for k, v in original_quota_set.items() if k in QUOTA_KEYS)
        cls.addClassResourceCleanup(cls.admin_quotas_client.update_quota_set,
                                    cls.demo_tenant_id, **cleanup_quota_set)

        # NOTE(gfidente): no need to delete in tearDown as
        # they are created using utility wrapper methods.
        cls.volume = cls.create_volume()

    @decorators.attr(type='negative')
    @decorators.idempotent_id('bf544854-d62a-47f2-a681-90f7a47d86b6')
    def test_quota_volumes(self):
        self.admin_quotas_client.update_quota_set(self.demo_tenant_id,
                                                  volumes=1, gigabytes=-1)
        self.assertRaises(lib_exc.OverLimit,
                          self.volumes_client.create_volume,
                          size=CONF.volume.volume_size)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('2dc27eee-8659-4298-b900-169d71a91374')
    def test_quota_volume_gigabytes(self):
        self.admin_quotas_client.update_quota_set(
            self.demo_tenant_id, gigabytes=CONF.volume.volume_size, volumes=-1)
        self.assertRaises(lib_exc.OverLimit,
                          self.volumes_client.create_volume,
                          size=CONF.volume.volume_size * 2)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d321dc21-d8c6-401f-95fe-49f4845f1a6d')
    def test_volume_extend_gigabytes_quota_deviation(self):
        self.admin_quotas_client.update_quota_set(
            self.demo_tenant_id, gigabytes=CONF.volume.volume_size)
        self.assertRaises(lib_exc.OverLimit,
                          self.volumes_client.extend_volume,
                          self.volume['id'],
                          new_size=CONF.volume.volume_size * 2)
