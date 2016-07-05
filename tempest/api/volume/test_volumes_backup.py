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

    @classmethod
    def resource_setup(cls):
        super(VolumesBackupsV2Test, cls).resource_setup()

        cls.volume = cls.create_volume()

    @test.idempotent_id('07af8f6d-80af-44c9-a5dc-c8427b1b62e6')
    @test.services('compute')
    def test_backup_create_attached_volume(self):
        """Test backup create using force flag.

        Cinder allows to create a volume backup, whether the volume status
        is "available" or "in-use".
        """
        # Create a server
        server_name = data_utils.rand_name('instance')
        server = self.create_server(name=server_name, wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        # Attach volume to instance
        self.servers_client.attach_volume(server['id'],
                                          volumeId=self.volume['id'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       self.volume['id'], 'in-use')
        self.addCleanup(waiters.wait_for_volume_status, self.volumes_client,
                        self.volume['id'], 'available')
        self.addCleanup(self.servers_client.detach_volume, server['id'],
                        self.volume['id'])
        # Create backup using force flag
        backup_name = data_utils.rand_name('Backup')
        backup = self.backups_client.create_backup(
            volume_id=self.volume['id'],
            name=backup_name, force=True)['backup']
        self.addCleanup(self.backups_client.delete_backup, backup['id'])
        self.backups_client.wait_for_backup_status(backup['id'],
                                                   'available')
        self.assertEqual(backup_name, backup['name'])


class VolumesBackupsV1Test(VolumesBackupsV2Test):
    _api_version = 1
