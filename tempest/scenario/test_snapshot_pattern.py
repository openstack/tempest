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

import testtools

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF


class TestSnapshotPattern(manager.ScenarioTest):
    """This test is for snapshotting an instance and booting with it.

    The following is the scenario outline:
     * boot an instance and create a timestamp file in it
     * snapshot the instance
     * boot a second instance from the snapshot
     * check the existence of the timestamp file in the second instance

    """

    @test.idempotent_id('608e604b-1d63-4a82-8e3e-91bc665c90b4')
    @testtools.skipUnless(CONF.compute_feature_enabled.snapshot,
                          'Snapshotting is not available.')
    @test.services('compute', 'network', 'image')
    def test_snapshot_pattern(self):
        # prepare for booting an instance
        keypair = self.create_keypair()
        security_group = self._create_security_group()

        # boot an instance and create a timestamp file in it
        server = self.create_server(
            image_id=CONF.compute.image_ref,
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}],
            wait_until='ACTIVE')

        instance_ip = self.get_server_ip(server)
        timestamp = self.create_timestamp(instance_ip,
                                          private_key=keypair['private_key'])

        # snapshot the instance
        snapshot_image = self.create_server_snapshot(server=server)

        # boot a second instance from the snapshot
        server_from_snapshot = self.create_server(
            image_id=snapshot_image['id'],
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}],
            wait_until='ACTIVE')

        # check the existence of the timestamp file in the second instance
        server_from_snapshot_ip = self.get_server_ip(server_from_snapshot)
        timestamp2 = self.get_timestamp(server_from_snapshot_ip,
                                        private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)
