# Copyright 2018 Red Hat, Inc.
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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestVolumeBackupRestore(manager.ScenarioTest):
    """Test cinder backup and restore

    This testcase verifies content preservation after backup and restore
    operations by booting a server from a restored backup and check the
    connectivity to it.

    The following is the scenario outline:
    1. Create volume from image.
    2. Create a backup for the volume.
    3. Restore the backup.
    4. Boot a server from the restored backup.
    5. Create a floating ip.
    6. Check server connectivity.
    """

    @classmethod
    def skip_checks(cls):
        super(TestVolumeBackupRestore, cls).skip_checks()
        if not CONF.volume_feature_enabled.backup:
            raise cls.skipException('Backup is not enable.')

    @decorators.idempotent_id('2ce5e55c-4085-43c1-98c6-582525334ad7')
    @decorators.attr(type='slow')
    @utils.services('compute', 'volume', 'image')
    def test_volume_backup_restore(self):
        # Create volume from image
        img_uuid = CONF.compute.image_ref
        volume = self.create_volume(imageRef=img_uuid)
        volume_details = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual('true', volume_details['bootable'])

        # Create a backup
        backup = self.create_backup(volume_id=volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Restore the backup
        restored_volume_id = self.restore_backup(backup['id'])['volume_id']

        # Verify the restored backup volume is bootable
        restored_volume_info = self.volumes_client.show_volume(
            restored_volume_id)['volume']
        self.assertEqual('true', restored_volume_info['bootable'])

        # Create keypair and security group
        keypair = self.create_keypair()
        security_group = self.create_security_group()

        # Boot a server from the restored backup
        bd_map_v2 = [{
            'uuid': restored_volume_id,
            'source_type': 'volume',
            'destination_type': 'volume',
            'boot_index': 0}]
        server = self.create_server(image_id='',
                                    block_device_mapping_v2=bd_map_v2,
                                    key_name=keypair['name'],
                                    security_groups=[
                                        {'name': security_group['name']}])

        # Create a floating ip and associate it to server.
        fip = self.create_floating_ip(server)
        floating_ip = self.associate_floating_ip(fip, server)
        # Check server connectivity
        self.check_vm_connectivity(floating_ip['floating_ip_address'],
                                   username=CONF.validation.image_ssh_user,
                                   private_key=keypair['private_key'],
                                   should_connect=True)
