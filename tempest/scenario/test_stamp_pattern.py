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

from oslo_log import log as logging
import testtools

from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestStampPattern(manager.ScenarioTest):
    """The test suite for both snapshoting and attaching of volume

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

    @classmethod
    def skip_checks(cls):
        super(TestStampPattern, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    def _wait_for_volume_available_on_the_system(self, ip_address,
                                                 private_key):
        ssh = self.get_remote_client(ip_address, private_key=private_key)

        def _func():
            disks = ssh.get_disks()
            LOG.debug("Disks: %s", disks)
            return CONF.compute.volume_device_name in disks

        if not test_utils.call_until_true(_func,
                                          CONF.compute.build_timeout,
                                          CONF.compute.build_interval):
            raise lib_exc.TimeoutException

    @decorators.attr(type='slow')
    @decorators.idempotent_id('10fd234a-515c-41e5-b092-8323060598c5')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @utils.services('compute', 'network', 'volume', 'image')
    def test_stamp_pattern(self):
        # prepare for booting an instance
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # boot an instance and create a timestamp file in it
        volume = self.create_volume()
        server = self.create_server(
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}])

        # create and add floating IP to server1
        ip_for_server = self.get_server_ip(server)

        # Make sure the machine ssh-able before attaching the volume
        self.get_remote_client(ip_for_server,
                               private_key=keypair['private_key'],
                               server=server)

        self.nova_volume_attach(server, volume)
        self._wait_for_volume_available_on_the_system(ip_for_server,
                                                      keypair['private_key'])
        timestamp = self.create_timestamp(ip_for_server,
                                          CONF.compute.volume_device_name,
                                          private_key=keypair['private_key'],
                                          server=server)
        self.nova_volume_detach(server, volume)

        # snapshot the volume
        volume_snapshot = self.create_volume_snapshot(volume['id'])

        # snapshot the instance
        snapshot_image = self.create_server_snapshot(server=server)

        # create second volume from the snapshot(volume2)
        volume_from_snapshot = self.create_volume(
            snapshot_id=volume_snapshot['id'])

        # boot second instance from the snapshot(instance2)
        server_from_snapshot = self.create_server(
            image_id=snapshot_image['id'],
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}])

        # create and add floating IP to server_from_snapshot
        ip_for_snapshot = self.get_server_ip(server_from_snapshot)

        # Make sure the machine ssh-able before attaching the volume
        # Just a live machine is responding
        # for device attache/detach as expected
        self.get_remote_client(ip_for_snapshot,
                               private_key=keypair['private_key'],
                               server=server_from_snapshot)

        # attach volume2 to instance2
        self.nova_volume_attach(server_from_snapshot, volume_from_snapshot)
        self._wait_for_volume_available_on_the_system(ip_for_snapshot,
                                                      keypair['private_key'])

        # check the existence of the timestamp file in the volume2
        timestamp2 = self.get_timestamp(ip_for_snapshot,
                                        CONF.compute.volume_device_name,
                                        private_key=keypair['private_key'],
                                        server=server_from_snapshot)
        self.assertEqual(timestamp, timestamp2)
