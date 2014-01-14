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

from tempest.openstack.common import log
from tempest.scenario import manager
from tempest.test import services


LOG = log.getLogger(__name__)


class TestSnapshotPattern(manager.OfficialClientTest):
    """
    This test is for snapshotting an instance and booting with it.
    The following is the scenario outline:
     * boot a instance and create a timestamp file in it
     * snapshot the instance
     * boot a second instance from the snapshot
     * check the existence of the timestamp file in the second instance

    """

    def _boot_image(self, image_id):
        create_kwargs = {
            'key_name': self.keypair.name
        }
        return self.create_server(image=image_id, create_kwargs=create_kwargs)

    def _add_keypair(self):
        self.keypair = self.create_keypair()

    def _ssh_to_server(self, server_or_ip):
        try:
            linux_client = self.get_remote_client(server_or_ip)
        except Exception:
            LOG.exception()
            self._log_console_output()
        return linux_client.ssh_client

    def _write_timestamp(self, server_or_ip):
        ssh_client = self._ssh_to_server(server_or_ip)
        ssh_client.exec_command('date > /tmp/timestamp; sync')
        self.timestamp = ssh_client.exec_command('cat /tmp/timestamp')

    def _check_timestamp(self, server_or_ip):
        ssh_client = self._ssh_to_server(server_or_ip)
        got_timestamp = ssh_client.exec_command('cat /tmp/timestamp')
        self.assertEqual(self.timestamp, got_timestamp)

    def _create_floating_ip(self):
        floating_ip = self.compute_client.floating_ips.create()
        self.addCleanup(floating_ip.delete)
        return floating_ip

    def _set_floating_ip_to_server(self, server, floating_ip):
        server.add_floating_ip(floating_ip)

    @services('compute', 'network', 'image')
    def test_snapshot_pattern(self):
        # prepare for booting a instance
        self._add_keypair()
        self._create_loginable_secgroup_rule_nova()

        # boot a instance and create a timestamp file in it
        server = self._boot_image(self.config.compute.image_ref)
        if self.config.compute.use_floatingip_for_ssh:
            fip_for_server = self._create_floating_ip()
            self._set_floating_ip_to_server(server, fip_for_server)
            self._write_timestamp(fip_for_server.ip)
        else:
            self._write_timestamp(server)

        # snapshot the instance
        snapshot_image = self.create_server_snapshot(server=server)

        # boot a second instance from the snapshot
        server_from_snapshot = self._boot_image(snapshot_image.id)

        # check the existence of the timestamp file in the second instance
        if self.config.compute.use_floatingip_for_ssh:
            fip_for_snapshot = self._create_floating_ip()
            self._set_floating_ip_to_server(server_from_snapshot,
                                            fip_for_snapshot)
            self._check_timestamp(fip_for_snapshot.ip)
        else:
            self._check_timestamp(server_from_snapshot)
