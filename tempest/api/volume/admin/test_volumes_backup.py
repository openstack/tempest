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
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class VolumesBackupsTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumesBackupsTest, cls).setUpClass()

        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

        cls.volumes_adm_client = cls.os_adm.volumes_client
        cls.backups_adm_client = cls.os_adm.backups_client
        cls.volume = cls.create_volume()

    @test.attr(type='smoke')
    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        # Create backup
        backup_name = data_utils.rand_name('Backup')
        create_backup = self.backups_adm_client.create_backup
        _, backup = create_backup(self.volume['id'],
                                  name=backup_name)
        self.addCleanup(self.backups_adm_client.delete_backup,
                        backup['id'])
        self.assertEqual(backup_name, backup['name'])
        self.volumes_adm_client.wait_for_volume_status(self.volume['id'],
                                                       'available')
        self.backups_adm_client.wait_for_backup_status(backup['id'],
                                                       'available')

        # Get a given backup
        _, backup = self.backups_adm_client.get_backup(backup['id'])
        self.assertEqual(backup_name, backup['name'])

        # Get all backups with detail
        _, backups = self.backups_adm_client.list_backups_with_detail()
        self.assertIn((backup['name'], backup['id']),
                      [(m['name'], m['id']) for m in backups])

        # Restore backup
        _, restore = self.backups_adm_client.restore_backup(backup['id'])

        # Delete backup
        self.addCleanup(self.volumes_adm_client.delete_volume,
                        restore['volume_id'])
        self.assertEqual(backup['id'], restore['backup_id'])
        self.backups_adm_client.wait_for_backup_status(backup['id'],
                                                       'available')
        self.volumes_adm_client.wait_for_volume_status(restore['volume_id'],
                                                       'available')
