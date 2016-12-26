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

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesBackupsV2Test(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesBackupsV2Test, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

    def restore_backup(self, backup_id):
        # Restore a backup
        restored_volume = self.backups_client.restore_backup(
            backup_id)['restore']

        # Delete backup
        self.addCleanup(self.volumes_client.delete_volume,
                        restored_volume['volume_id'])
        self.assertEqual(backup_id, restored_volume['backup_id'])
        waiters.wait_for_backup_status(self.backups_client,
                                       backup_id, 'available')
        waiters.wait_for_volume_status(self.volumes_client,
                                       restored_volume['volume_id'],
                                       'available')
        return restored_volume

    @test.idempotent_id('a66eb488-8ee1-47d4-8e9f-575a095728c6')
    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        # Create backup
        volume = self.create_volume()
        self.addCleanup(self.volumes_client.delete_volume,
                        volume['id'])
        backup_name = data_utils.rand_name(
            self.__class__.__name__ + '-Backup')
        description = data_utils.rand_name("volume-backup-description")
        backup = self.create_backup(volume_id=volume['id'],
                                    name=backup_name,
                                    description=description)
        self.assertEqual(backup_name, backup['name'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')

        # Get a given backup
        backup = self.backups_client.show_backup(backup['id'])['backup']
        self.assertEqual(backup_name, backup['name'])
        self.assertEqual(description, backup['description'])

        # Get all backups with detail
        backups = self.backups_client.list_backups(
            detail=True)['backups']
        self.assertIn((backup['name'], backup['id']),
                      [(m['name'], m['id']) for m in backups])

        self.restore_backup(backup['id'])

    @test.idempotent_id('07af8f6d-80af-44c9-a5dc-c8427b1b62e6')
    @test.services('compute')
    def test_backup_create_attached_volume(self):
        """Test backup create using force flag.

        Cinder allows to create a volume backup, whether the volume status
        is "available" or "in-use".
        """
        # Create a server
        volume = self.create_volume()
        self.addCleanup(self.volumes_client.delete_volume,
                        volume['id'])
        server = self.create_server(wait_until='ACTIVE')
        # Attach volume to instance
        self.servers_client.attach_volume(server['id'],
                                          volumeId=volume['id'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'in-use')
        self.addCleanup(waiters.wait_for_volume_status, self.volumes_client,
                        volume['id'], 'available')
        self.addCleanup(self.servers_client.detach_volume, server['id'],
                        volume['id'])
        # Create backup using force flag
        backup_name = data_utils.rand_name(
            self.__class__.__name__ + '-Backup')
        backup = self.create_backup(volume_id=volume['id'],
                                    name=backup_name, force=True)
        self.assertEqual(backup_name, backup['name'])

    @test.idempotent_id('2a8ba340-dff2-4511-9db7-646f07156b15')
    def test_bootable_volume_backup_and_restore(self):
        # Create volume from image
        img_uuid = CONF.compute.image_ref
        volume = self.create_volume(imageRef=img_uuid)

        volume_details = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual('true', volume_details['bootable'])

        # Create a backup
        backup = self.create_backup(volume_id=volume['id'])

        # Restore the backup
        restored_volume_id = self.restore_backup(backup['id'])['volume_id']

        # Verify the restored backup volume is bootable
        restored_volume_info = self.volumes_client.show_volume(
            restored_volume_id)['volume']

        self.assertEqual('true', restored_volume_info['bootable'])


class VolumesBackupsV1Test(VolumesBackupsV2Test):
    _api_version = 1
