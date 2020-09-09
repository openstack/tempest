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

from oslo_serialization import base64
from oslo_serialization import jsonutils as json

from tempest.api.volume import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumesBackupsAdminTest(base.BaseVolumeAdminTest):
    """Test volume backups"""

    @classmethod
    def skip_checks(cls):
        super(VolumesBackupsAdminTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

    def _delete_backup(self, backup_id):
        self.admin_backups_client.delete_backup(backup_id)
        self.admin_backups_client.wait_for_resource_deletion(backup_id)

    def _decode_url(self, backup_url):
        return json.loads(base64.decode_as_text(backup_url))

    def _encode_backup(self, backup):
        retval = json.dumps(backup)
        return base64.encode_as_text(retval)

    def _modify_backup_url(self, backup_url, changes):
        backup = self._decode_url(backup_url)
        backup.update(changes)
        return self._encode_backup(backup)

    @decorators.idempotent_id('a99c54a1-dd80-4724-8a13-13bf58d4068d')
    def test_volume_backup_export_import(self):
        """Test backup export import functionality.

        Cinder allows exporting DB backup information through its API so it can
        be imported back in case of a DB loss.
        """
        volume = self.create_volume()
        # Create backup
        backup_name = data_utils.rand_name(self.__class__.__name__ + '-Backup')
        backup = self.create_backup(volume_id=volume['id'], name=backup_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.assertEqual(backup_name, backup['name'])

        # Export Backup
        export_backup = (self.admin_backups_client.export_backup(backup['id'])
                         ['backup-record'])
        self.assertTrue(export_backup['backup_service'].startswith(
                        'cinder.backup.drivers'))

        # NOTE(geguileo): Backups are imported with the same backup id
        # (important for incremental backups among other things), so we cannot
        # import the exported backup information as it is, because that Backup
        # ID already exists.  So we'll fake the data by changing the backup id
        # in the exported backup DB info we have retrieved before importing it
        # back.
        new_id = data_utils.rand_uuid()
        new_url = self._modify_backup_url(
            export_backup['backup_url'], {'id': new_id})

        # Import Backup
        import_backup = self.admin_backups_client.import_backup(
            backup_service=export_backup['backup_service'],
            backup_url=new_url)['backup']

        # NOTE(geguileo): We delete both backups, but only one of those
        # deletions will delete data from the backup back-end because they
        # were both pointing to the same backend data.
        self.addCleanup(self._delete_backup, new_id)
        self.assertEqual(new_id, import_backup['id'])
        waiters.wait_for_volume_resource_status(self.admin_backups_client,
                                                import_backup['id'],
                                                'available')

        # Verify Import Backup
        backups = self.admin_backups_client.list_backups()['backups']
        self.assertIn(new_id, [b['id'] for b in backups])

        # Restore backup
        restore = self.backups_client.restore_backup(backup['id'])['restore']
        self.addCleanup(self.volumes_client.delete_volume,
                        restore['volume_id'])
        self.assertEqual(backup['id'], restore['backup_id'])

        # When restore operation is performed then, backup['id']
        # goes to 'restoring' state so we need to wait for
        # backup['id'] to become 'available'.
        waiters.wait_for_volume_resource_status(
            self.backups_client, backup['id'], 'available')
        waiters.wait_for_volume_resource_status(
            self.volumes_client, restore['volume_id'], 'available')

        # Verify if restored volume is there in volume list
        volumes = self.volumes_client.list_volumes()['volumes']
        self.assertIn(restore['volume_id'], [v['id'] for v in volumes])

    @decorators.idempotent_id('47a35425-a891-4e13-961c-c45deea21e94')
    def test_volume_backup_reset_status(self):
        """Test resetting volume backup status to error"""
        # Create a volume
        volume = self.create_volume()
        # Create a backup
        backup_name = data_utils.rand_name(
            self.__class__.__name__ + '-Backup')
        backup = self.create_backup(volume_id=volume['id'], name=backup_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.assertEqual(backup_name, backup['name'])
        # Reset backup status to error
        self.admin_backups_client.reset_backup_status(backup_id=backup['id'],
                                                      status="error")
        waiters.wait_for_volume_resource_status(self.backups_client,
                                                backup['id'], 'error')
