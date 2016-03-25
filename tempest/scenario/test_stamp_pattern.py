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

from oslo_log import log as logging
import testtools

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.scenario import manager
from tempest import test

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

    def _create_volume_snapshot(self, volume):
        snapshot_name = data_utils.rand_name('scenario-snapshot')
        snapshot = self.snapshots_client.create_snapshot(
            volume_id=volume['id'], display_name=snapshot_name)['snapshot']

        def cleaner():
            self.snapshots_client.delete_snapshot(snapshot['id'])
            try:
                while self.snapshots_client.show_snapshot(
                        snapshot['id'])['snapshot']:
                    time.sleep(1)
            except lib_exc.NotFound:
                pass
        self.addCleanup(cleaner)
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')
        waiters.wait_for_snapshot_status(self.snapshots_client,
                                         snapshot['id'], 'available')
        self.assertEqual(snapshot_name, snapshot['display_name'])
        return snapshot

    def _wait_for_volume_available_on_the_system(self, ip_address,
                                                 private_key):
        ssh = self.get_remote_client(ip_address, private_key=private_key)

        def _func():
            part = ssh.get_partitions()
            LOG.debug("Partitions:%s" % part)
            return CONF.compute.volume_device_name in part

        if not test.call_until_true(_func,
                                    CONF.compute.build_timeout,
                                    CONF.compute.build_interval):
            raise exceptions.TimeoutException

    @decorators.skip_because(bug="1205344")
    @test.idempotent_id('10fd234a-515c-41e5-b092-8323060598c5')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    @test.services('compute', 'network', 'volume', 'image')
    def test_stamp_pattern(self):
        # prepare for booting an instance
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # boot an instance and create a timestamp file in it
        volume = self.create_volume()
        server = self.create_server(
            image_id=CONF.compute.image_ref,
            key_name=keypair['name'],
            security_groups=security_group,
            wait_until='ACTIVE')

        # create and add floating IP to server1
        ip_for_server = self.get_server_ip(server)

        self.nova_volume_attach(server, volume)
        self._wait_for_volume_available_on_the_system(ip_for_server,
                                                      keypair['private_key'])
        timestamp = self.create_timestamp(ip_for_server,
                                          CONF.compute.volume_device_name,
                                          private_key=keypair['private_key'])
        self.nova_volume_detach(server, volume)

        # snapshot the volume
        volume_snapshot = self._create_volume_snapshot(volume)

        # snapshot the instance
        snapshot_image = self.create_server_snapshot(server=server)

        # create second volume from the snapshot(volume2)
        volume_from_snapshot = self.create_volume(
            snapshot_id=volume_snapshot['id'])

        # boot second instance from the snapshot(instance2)
        server_from_snapshot = self.create_server(
            image_id=snapshot_image['id'],
            key_name=keypair['name'],
            security_groups=security_group)

        # create and add floating IP to server_from_snapshot
        ip_for_snapshot = self.get_server_ip(server_from_snapshot)

        # attach volume2 to instance2
        self.nova_volume_attach(server_from_snapshot, volume_from_snapshot)
        self._wait_for_volume_available_on_the_system(ip_for_snapshot,
                                                      keypair['private_key'])

        # check the existence of the timestamp file in the volume2
        timestamp2 = self.get_timestamp(ip_for_snapshot,
                                        CONF.compute.volume_device_name,
                                        private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)
