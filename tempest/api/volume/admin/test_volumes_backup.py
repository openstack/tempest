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
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest import test

CONF = config.CONF


class VolumesBackupsV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesBackupsV2Test, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumesBackupsV2Test, cls).resource_setup()

        cls.volume = cls.create_volume()

    def _delete_backup(self, backup_id):
        self.backups_adm_client.delete_backup(backup_id)
        self.backups_adm_client.wait_for_backup_deletion(backup_id)

    @test.idempotent_id('a66eb488-8ee1-47d4-8e9f-575a095728c6')
    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        # Create backup
        backup_name = data_utils.rand_name('Backup')
        create_backup = self.backups_adm_client.create_backup
        backup = create_backup(volume_id=self.volume['id'],
                               name=backup_name)['backup']
        self.addCleanup(self.backups_adm_client.delete_backup,
                        backup['id'])
        self.assertEqual(backup_name, backup['name'])
        waiters.wait_for_volume_status(self.admin_volume_client,
                                       self.volume['id'], 'available')
        self.backups_adm_client.wait_for_backup_status(backup['id'],
                                                       'available')

        # Get a given backup
        backup = self.backups_adm_client.show_backup(backup['id'])['backup']
        self.assertEqual(backup_name, backup['name'])

        # Get all backups with detail
        backups = self.backups_adm_client.list_backups(detail=True)['backups']
        self.assertIn((backup['name'], backup['id']),
                      [(m['name'], m['id']) for m in backups])

        # Restore backup
        restore = self.backups_adm_client.restore_backup(
            backup['id'])['restore']

        # Delete backup
        self.addCleanup(self.admin_volume_client.delete_volume,
                        restore['volume_id'])
        self.assertEqual(backup['id'], restore['backup_id'])
        self.backups_adm_client.wait_for_backup_status(backup['id'],
                                                       'available')
        waiters.wait_for_volume_status(self.admin_volume_client,
                                       restore['volume_id'], 'available')

    @decorators.skip_because(bug='1455043')
    @test.idempotent_id('a99c54a1-dd80-4724-8a13-13bf58d4068d')
    def test_volume_backup_export_import(self):
        # Create backup
        backup_name = data_utils.rand_name('Backup')
        backup = (self.backups_adm_client.create_backup(
            volume_id=self.volume['id'], name=backup_name)['backup'])
        self.addCleanup(self._delete_backup, backup['id'])
        self.assertEqual(backup_name, backup['name'])
        self.backups_adm_client.wait_for_backup_status(backup['id'],
                                                       'available')

        # Export Backup
        export_backup = (self.backups_adm_client.export_backup(backup['id'])
                         ['backup-record'])
        self.assertIn('backup_service', export_backup)
        self.assertIn('backup_url', export_backup)
        self.assertTrue(export_backup['backup_service'].startswith(
                        'cinder.backup.drivers'))
        self.assertIsNotNone(export_backup['backup_url'])

        # Import Backup
        import_backup = self.backups_adm_client.import_backup(
            backup_service=export_backup['backup_service'],
            backup_url=export_backup['backup_url'])['backup']
        self.addCleanup(self._delete_backup, import_backup['id'])
        self.assertIn("id", import_backup)
        self.backups_adm_client.wait_for_backup_status(import_backup['id'],
                                                       'available')

        # Verify Import Backup
        backups = self.backups_adm_client.list_backups(detail=True)['backups']
        self.assertIn(import_backup['id'], [b['id'] for b in backups])

        # Restore backup
        restore = (self.backups_adm_client.restore_backup(import_backup['id'])
                   ['restore'])
        self.addCleanup(self.admin_volume_client.delete_volume,
                        restore['volume_id'])
        self.assertEqual(import_backup['id'], restore['backup_id'])
        waiters.wait_for_volume_status(self.admin_volume_client,
                                       restore['volume_id'], 'available')

        # Verify if restored volume is there in volume list
        volumes = self.admin_volume_client.list_volumes()['volumes']
        self.assertIn(restore['volume_id'], [v['id'] for v in volumes])
        self.backups_adm_client.wait_for_backup_status(import_backup['id'],
                                                       'available')


class VolumesBackupsV1Test(VolumesBackupsV2Test):
    _api_version = 1
