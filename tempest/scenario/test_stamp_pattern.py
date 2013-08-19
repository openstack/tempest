# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NEC Corporation
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

import time

from cinderclient import exceptions as cinder_exceptions
import testtools

from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager
import tempest.test

LOG = logging.getLogger(__name__)


class TestStampPattern(manager.OfficialClientTest):
    """
    This test is for snapshotting an instance/volume and attaching the volume
    created from snapshot to the instance booted from snapshot.
    The following is the scenario outline:
    1. Boot an instance "instance1"
    2. Create a volume "volume1"
    3. Attach volume1 to instance1
    4. Create a filesystem on volume1
    5. Mount volume1
    6. Create a file which timestamp is written in volume1
    7. Unmount volume1
    8. Detach volume1 from instance1
    9. Get a snapshot "snapshot_from_volume" of volume1
    10. Get a snapshot "snapshot_from_instance" of instance1
    11. Boot an instance "instance2" from snapshot_from_instance
    12. Create a volume "volume2"  from snapshot_from_volume
    13. Attach volume2 to instance2
    14. Check the existence of a file which created at 6. in volume2
    """

    def _wait_for_server_status(self, server, status):
        self.status_timeout(self.compute_client.servers,
                            server.id,
                            status)

    def _wait_for_image_status(self, image_id, status):
        self.status_timeout(self.image_client.images, image_id, status)

    def _wait_for_volume_snapshot_status(self, volume_snapshot, status):
        self.status_timeout(self.volume_client.volume_snapshots,
                            volume_snapshot.id, status)

    def _boot_image(self, image_id):
        create_kwargs = {
            'key_name': self.keypair.name
        }
        return self.create_server(self.compute_client, image=image_id,
                                  create_kwargs=create_kwargs)

    def _add_keypair(self):
        self.keypair = self.create_keypair()

    def _create_floating_ip(self):
        floating_ip = self.compute_client.floating_ips.create()
        self.addCleanup(floating_ip.delete)
        return floating_ip

    def _add_floating_ip(self, server, floating_ip):
        server.add_floating_ip(floating_ip)

    def _remote_client_to_server(self, server_or_ip):
        if isinstance(server_or_ip, basestring):
            ip = server_or_ip
        else:
            network_name_for_ssh = self.config.compute.network_for_ssh
            ip = server_or_ip.networks[network_name_for_ssh][0]
        username = self.config.scenario.ssh_user
        linux_client = RemoteClient(ip,
                                    username,
                                    pkey=self.keypair.private_key)
        return linux_client

    def _ssh_to_server(self, server_or_ip):
        linux_client = self._remote_client_to_server(server_or_ip)
        return linux_client.ssh_client

    def _create_image(self, server):
        snapshot_name = rand_name('scenario-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.image_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'active')
        snapshot_image = self.image_client.images.get(image_id)
        self.assertEquals(snapshot_name, snapshot_image.name)
        return image_id

    def _create_volume_snapshot(self, volume):
        snapshot_name = rand_name('scenario-snapshot-')
        volume_snapshots = self.volume_client.volume_snapshots
        snapshot = volume_snapshots.create(
            volume.id, display_name=snapshot_name)

        def cleaner():
            volume_snapshots.delete(snapshot)
            try:
                while volume_snapshots.get(snapshot.id):
                    time.sleep(1)
            except cinder_exceptions.NotFound:
                pass
        self.addCleanup(cleaner)
        self._wait_for_volume_status(volume, 'available')
        self._wait_for_volume_snapshot_status(snapshot, 'available')
        self.assertEquals(snapshot_name, snapshot.display_name)
        return snapshot

    def _wait_for_volume_status(self, volume, status):
        self.status_timeout(
            self.volume_client.volumes, volume.id, status)

    def _create_volume(self, snapshot_id=None):
        return self.create_volume(snapshot_id=snapshot_id)

    def _attach_volume(self, server, volume):
        attach_volume_client = self.compute_client.volumes.create_server_volume
        attached_volume = attach_volume_client(server.id,
                                               volume.id,
                                               '/dev/vdb')
        self.assertEqual(volume.id, attached_volume.id)
        self._wait_for_volume_status(attached_volume, 'in-use')

    def _detach_volume(self, server, volume):
        detach_volume_client = self.compute_client.volumes.delete_server_volume
        detach_volume_client(server.id, volume.id)
        self._wait_for_volume_status(volume, 'available')

    def _wait_for_volume_availible_on_the_system(self, server_or_ip):
        ssh = self._remote_client_to_server(server_or_ip)
        conf = self.config

        def _func():
            part = ssh.get_partitions()
            LOG.debug("Partitions:%s" % part)
            return 'vdb' in part

        if not tempest.test.call_until_true(_func,
                                            conf.compute.build_timeout,
                                            conf.compute.build_interval):
            raise exceptions.TimeoutException

    def _create_timestamp(self, server_or_ip):
        ssh_client = self._ssh_to_server(server_or_ip)
        ssh_client.exec_command('sudo /usr/sbin/mkfs.ext4 /dev/vdb')
        ssh_client.exec_command('sudo mount /dev/vdb /mnt')
        ssh_client.exec_command('sudo sh -c "date > /mnt/timestamp;sync"')
        self.timestamp = ssh_client.exec_command('sudo cat /mnt/timestamp')
        ssh_client.exec_command('sudo umount /mnt')

    def _check_timestamp(self, server_or_ip):
        ssh_client = self._ssh_to_server(server_or_ip)
        ssh_client.exec_command('sudo mount /dev/vdb /mnt')
        got_timestamp = ssh_client.exec_command('sudo cat /mnt/timestamp')
        self.assertEqual(self.timestamp, got_timestamp)

    @testtools.skip("Until Bug #1205344 is fixed")
    def test_stamp_pattern(self):
        # prepare for booting a instance
        self._add_keypair()
        self.create_loginable_secgroup_rule()

        # boot an instance and create a timestamp file in it
        volume = self._create_volume()
        server = self._boot_image(self.config.compute.image_ref)

        # create and add floating IP to server1
        if self.config.compute.use_floatingip_for_ssh:
            floating_ip_for_server = self._create_floating_ip()
            self._add_floating_ip(server, floating_ip_for_server)
            ip_for_server = floating_ip_for_server.ip
        else:
            ip_for_server = server

        self._attach_volume(server, volume)
        self._wait_for_volume_availible_on_the_system(ip_for_server)
        self._create_timestamp(ip_for_server)
        self._detach_volume(server, volume)

        # snapshot the volume
        volume_snapshot = self._create_volume_snapshot(volume)

        # snapshot the instance
        snapshot_image_id = self._create_image(server)

        # create second volume from the snapshot(volume2)
        volume_from_snapshot = self._create_volume(
            snapshot_id=volume_snapshot.id)

        # boot second instance from the snapshot(instance2)
        server_from_snapshot = self._boot_image(snapshot_image_id)

        # create and add floating IP to server_from_snapshot
        if self.config.compute.use_floatingip_for_ssh:
            floating_ip_for_snapshot = self._create_floating_ip()
            self._add_floating_ip(server_from_snapshot,
                                  floating_ip_for_snapshot)
            ip_for_snapshot = floating_ip_for_snapshot.ip
        else:
            ip_for_snapshot = server_from_snapshot

        # attach volume2 to instance2
        self._attach_volume(server_from_snapshot, volume_from_snapshot)
        self._wait_for_volume_availible_on_the_system(ip_for_snapshot)

        # check the existence of the timestamp file in the volume2
        self._check_timestamp(ip_for_snapshot)
