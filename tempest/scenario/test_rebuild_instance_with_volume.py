# Copyright 2016 Mirantis Inc.
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

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF


class TestRebuildInstanceWithVolume(manager.ScenarioTest):
    """Verifying functionality of rebuilding instance with attached volume

    The following is the scenario outline:
    1. Boot an instance
    2. Create a volume
    3. Attach the volume to the instance
    4. Create a file with timestamp on the volume
    5. Rebuild the instance
    6. Check existence of the file which was created at step #4
    7. Detach the volume
    """

    @test.idempotent_id('36c3d492-f5bd-11e4-b9b2-1697f925ec7b')
    @test.services('compute', 'volume', 'image', 'network')
    def test_rebuild_instance_with_volume(self):
        # create key pair and security group
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # boot an instance
        server = self.create_server(
            image_id=CONF.compute.image_ref,
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}],
            wait_until='ACTIVE')

        # get instance IP
        server_ip = self.get_server_ip(server)

        # create volume, attach it and create timestamp file on it
        volume = self.create_volume()
        attached_volume = self.nova_volume_attach(server, volume)
        timestamp = self.create_timestamp(
            server_ip,
            dev_name=CONF.compute.volume_device_name,
            private_key=keypair['private_key'])

        # NOTE: for rebuild we use the same image,
        # so we should verify that VM was actually rebuilt
        ssh_client = self.get_remote_client(server_ip,
                                            private_key=keypair['private_key'])
        cmd_addstamp = 'sudo sh -c "echo \'#check_rebuild\' >> /etc/fstab"'
        fstab = ssh_client.exec_command('%s; cat /etc/fstab' % cmd_addstamp)

        # rebuild instance
        self.rebuild_server(server['id'])

        # verify that instance was actually rebuilt
        actual_fstab = ssh_client.exec_command('cat /etc/fstab')
        self.assertNotEqual(fstab, actual_fstab, 'Server was not rebuilt')

        # check existence of the timestamp file in the volume
        timestamp2 = self.get_timestamp(
            server_ip,
            dev_name=CONF.compute.volume_device_name,
            private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)

        # detach volume
        self.nova_volume_detach(server, attached_volume)
