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

    @test.idempotent_id('a66eb488-8ee1-47d4-8e9f-575a095728c6')
    def test_volume_backup_create_get_detailed_list_restore_delete(self):
        # Create backup
        volume = self.create_volume()
        self.addCleanup(self.volumes_client.delete_volume,
                        volume['id'])
        backup_name = data_utils.rand_name(
            self.__class__.__name__ + '-Backup')
        create_backup = self.backups_client.create_backup
        backup = create_backup(volume_id=volume['id'],
                               name=backup_name)['backup']
        self.addCleanup(self.backups_client.delete_backup,
                        backup['id'])
        self.assertEqual(backup_name, backup['name'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')
        self.backups_client.wait_for_backup_status(backup['id'],
                                                   'available')

        # Get a given backup
        backup = self.backups_client.show_backup(backup['id'])['backup']
        self.assertEqual(backup_name, backup['name'])

        # Get all backups with detail
        backups = self.backups_client.list_backups(
            detail=True)['backups']
        self.assertIn((backup['name'], backup['id']),
                      [(m['name'], m['id']) for m in backups])

        # Restore backup
        restore = self.backups_client.restore_backup(
            backup['id'])['restore']

        # Delete backup
        self.addCleanup(self.volumes_client.delete_volume,
                        restore['volume_id'])
        self.assertEqual(backup['id'], restore['backup_id'])
        self.backups_client.wait_for_backup_status(backup['id'],
                                                   'available')
        waiters.wait_for_volume_status(self.volumes_client,
                                       restore['volume_id'], 'available')

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
        server_name = data_utils.rand_name(
            self.__class__.__name__ + '-instance')
        server = self.create_server(name=server_name, wait_until='ACTIVE')
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
        backup = self.backups_client.create_backup(
            volume_id=volume['id'],
            name=backup_name, force=True)['backup']
        self.addCleanup(self.backups_client.delete_backup, backup['id'])
        self.backups_client.wait_for_backup_status(backup['id'],
                                                   'available')
        self.assertEqual(backup_name, backup['name'])


class VolumesBackupsV1Test(VolumesBackupsV2Test):
    _api_version = 1
