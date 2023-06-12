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

from testtools import matchers

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumesBackupsTest(base.BaseVolumeTest):
    """Test volumes backup"""

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(VolumesBackupsTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

    def restore_backup(self, backup_id):
        # Restore a backup
        restored_volume = self.backups_client.restore_backup(
            backup_id)['restore']

        # Delete backup
        self.addCleanup(self.delete_volume, self.volumes_client,
                        restored_volume['volume_id'])
        self.assertEqual(backup_id, restored_volume['backup_id'])
        waiters.wait_for_volume_resource_status(self.backups_client,
                                                backup_id, 'available')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                restored_volume['volume_id'],
                                                'available')
        return restored_volume

    @decorators.idempotent_id('a66eb488-8ee1-47d4-8e9f-575a095728c6')
    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        """Test create/get/list/restore/delete volume backup

        1. Create volume1 with metadata
        2. Create backup1 from volume1
        3. Show backup1
        4. List backups with detail
        5. Restore backup1
        6. Verify backup1 has been restored successfully with the metadata
           of volume1
        """
        # Create a volume with metadata
        metadata = {"vol-meta1": "value1",
                    "vol-meta2": "value2",
                    "vol-meta3": "value3"}
        volume = self.create_volume(metadata=metadata)
        self.addCleanup(self.delete_volume, self.volumes_client, volume['id'])

        # Create a backup
        kwargs = {}
        kwargs["name"] = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-Backup')
        kwargs["description"] = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name="backup-description")
        if CONF.volume.backup_driver == "swift":
            kwargs["container"] = data_utils.rand_name(
                prefix=CONF.resource_name_prefix,
                name=self.__class__.__name__ + '-backup-container').lower()
        backup = self.create_backup(volume_id=volume['id'], **kwargs)
        self.assertEqual(kwargs["name"], backup['name'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Get a given backup
        backup = self.backups_client.show_backup(backup['id'])['backup']
        self.assertEqual(kwargs["name"], backup['name'])
        self.assertEqual(kwargs["description"], backup['description'])
        if CONF.volume.backup_driver == "swift":
            self.assertEqual(kwargs["container"], backup['container'])

        # Get all backups with detail
        backups = self.backups_client.list_backups(detail=True)['backups']
        self.assertIn((backup['name'], backup['id']),
                      [(m['name'], m['id']) for m in backups])

        restored_volume = self.restore_backup(backup['id'])

        restored_volume_metadata = self.volumes_client.show_volume(
            restored_volume['volume_id'])['volume']['metadata']

        # Verify the backup has been restored successfully
        # with the metadata of the source volume.
        self.assertThat(restored_volume_metadata.items(),
                        matchers.ContainsAll(metadata.items()))

    @decorators.idempotent_id('07af8f6d-80af-44c9-a5dc-c8427b1b62e6')
    @utils.services('compute')
    def test_backup_create_attached_volume(self):
        """Test backup create using force flag.

        Cinder allows to create a volume backup, whether the volume status
        is "available" or "in-use".
        """
        # Create a server
        volume = self.create_volume(wait_until=False)
        self.addCleanup(self.delete_volume, self.volumes_client, volume['id'])
        validation_resources = self.get_test_validation_resources(
            self.os_primary)
        server = self.create_server(wait_until='SSHABLE',
                                    validation_resources=validation_resources,
                                    validatable=True)
        # Attach volume to instance
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.attach_volume(server['id'], volume['id'])
        # Create backup using force flag
        backup_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-Backup')
        backup = self.create_backup(volume_id=volume['id'],
                                    name=backup_name, force=True)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'in-use')
        self.assertEqual(backup_name, backup['name'])

    @decorators.idempotent_id('2a8ba340-dff2-4511-9db7-646f07156b15')
    @utils.services('image')
    def test_bootable_volume_backup_and_restore(self):
        """Test backuping and restoring a bootable volume

        1. Create volume1 from image
        2. Create backup1 from volume1
        3. Restore backup1
        4. Verify the restored backup volume is bootable
        """
        # Create volume from image
        img_uuid = CONF.compute.image_ref
        volume = self.create_volume(imageRef=img_uuid)

        volume_details = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertTrue(volume_details['bootable'])

        # Create a backup
        backup = self.create_backup(volume_id=volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Restore the backup
        restored_volume_id = self.restore_backup(backup['id'])['volume_id']

        # Verify the restored backup volume is bootable
        restored_volume_info = self.volumes_client.show_volume(
            restored_volume_id)['volume']

        self.assertTrue(restored_volume_info['bootable'])

    @decorators.idempotent_id('f86eff09-2a6d-43c1-905e-8079e5754f1e')
    @utils.services('compute')
    @decorators.related_bug('1703011')
    def test_volume_backup_incremental(self):
        """Test create a backup when latest incremental backup is deleted"""
        # Create a volume
        volume = self.create_volume()

        # Create a server
        server = self.create_server(wait_until='SSHABLE')

        # Attach volume to the server
        self.attach_volume(server['id'], volume['id'])

        # Create a backup to the attached volume
        backup1 = self.create_backup(volume['id'], force=True)

        # Validate backup details
        backup_info = self.backups_client.show_backup(backup1['id'])['backup']
        self.assertEqual(False, backup_info['has_dependent_backups'])
        self.assertEqual(False, backup_info['is_incremental'])

        # Create another incremental backup
        backup2 = self.backups_client.create_backup(
            volume_id=volume['id'], incremental=True, force=True)['backup']
        waiters.wait_for_volume_resource_status(self.backups_client,
                                                backup2['id'], 'available')

        # Validate incremental backup details
        backup2_info = self.backups_client.show_backup(backup2['id'])['backup']
        self.assertEqual(True, backup2_info['is_incremental'])
        self.assertEqual(False, backup2_info['has_dependent_backups'])

        # Delete the last incremental backup that was created
        self.backups_client.delete_backup(backup2['id'])
        self.backups_client.wait_for_resource_deletion(backup2['id'])

        # Create another incremental backup
        backup3 = self.create_backup(
            volume_id=volume['id'], incremental=True, force=True)

        # Validate incremental backup details
        backup3_info = self.backups_client.show_backup(backup3['id'])['backup']
        self.assertEqual(True, backup3_info['is_incremental'])
        self.assertEqual(False, backup3_info['has_dependent_backups'])


class VolumesBackupsV39Test(base.BaseVolumeTest):
    """Test volumes backup with volume microversion greater than 3.8"""

    volume_min_microversion = '3.9'
    volume_max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(VolumesBackupsV39Test, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException("Cinder backup feature disabled")

    @decorators.idempotent_id('9b374cbc-be5f-4d37-8848-7efb8a873dcc')
    def test_update_backup(self):
        """Test updating backup's name and description"""
        # Create volume and backup
        volume = self.create_volume()
        backup = self.create_backup(volume_id=volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Update backup and assert response body for update_backup method
        update_kwargs = {
            'name': data_utils.rand_name(
                prefix=CONF.resource_name_prefix,
                name=self.__class__.__name__ + '-Backup'),
            'description': data_utils.rand_name(
                prefix=CONF.resource_name_prefix,
                name="volume-backup-description")
        }
        update_backup = self.backups_client.update_backup(
            backup['id'], **update_kwargs)['backup']
        self.assertEqual(backup['id'], update_backup['id'])
        self.assertEqual(update_kwargs['name'], update_backup['name'])

        # Assert response body for show_backup method
        retrieved_backup = self.backups_client.show_backup(
            backup['id'])['backup']
        for key in update_kwargs:
            self.assertEqual(update_kwargs[key], retrieved_backup[key])
