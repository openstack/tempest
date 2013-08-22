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

from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest.openstack.common import log as logging
from tempest.scenario import manager


LOG = logging.getLogger(__name__)


class TestSnapshotPattern(manager.OfficialClientTest):
    """
    This test is for snapshotting an instance and booting with it.
    The following is the scenario outline:
     * boot a instance and create a timestamp file in it
     * snapshot the instance
     * boot a second instance from the snapshot
     * check the existence of the timestamp file in the second instance

    """

    def _wait_for_server_status(self, server, status):
        self.status_timeout(self.compute_client.servers,
                            server.id,
                            status)

    def _wait_for_image_status(self, image_id, status):
        self.status_timeout(self.image_client.images, image_id, status)

    def _boot_image(self, image_id):
        create_kwargs = {
            'key_name': self.keypair.name
        }
        return self.create_server(self.compute_client, image=image_id,
                                  create_kwargs=create_kwargs)

    def _add_keypair(self):
        self.keypair = self.create_keypair()

    def _create_security_group_rule(self):
        sgs = self.compute_client.security_groups.list()
        for sg in sgs:
            if sg.name == 'default':
                secgroup = sg

        ruleset = {
            # ssh
            'ip_protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr': '0.0.0.0/0',
            'group_id': None
        }
        sg_rule = self.compute_client.security_group_rules.create(secgroup.id,
                                                                  **ruleset)
        self.addCleanup(self.compute_client.security_group_rules.delete,
                        sg_rule.id)

    def _ssh_to_server(self, server_or_ip):
        if isinstance(server_or_ip, basestring):
            ip = server_or_ip
        else:
            network_name_for_ssh = self.config.compute.network_for_ssh
            ip = server_or_ip.networks[network_name_for_ssh][0]
        username = self.config.scenario.ssh_user
        linux_client = RemoteClient(ip,
                                    username,
                                    pkey=self.keypair.private_key)

        return linux_client.ssh_client

    def _write_timestamp(self, server_or_ip):
        ssh_client = self._ssh_to_server(server_or_ip)
        ssh_client.exec_command('date > /tmp/timestamp; sync')
        self.timestamp = ssh_client.exec_command('cat /tmp/timestamp')

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

    def test_snapshot_pattern(self):
        # prepare for booting a instance
        self._add_keypair()
        self._create_security_group_rule()

        # boot a instance and create a timestamp file in it
        server = self._boot_image(self.config.compute.image_ref)
        if self.config.compute.use_floatingip_for_ssh:
            fip_for_server = self._create_floating_ip()
            self._set_floating_ip_to_server(server, fip_for_server)
            self._write_timestamp(fip_for_server.ip)
        else:
            self._write_timestamp(server)

        # snapshot the instance
        snapshot_image_id = self._create_image(server)

        # boot a second instance from the snapshot
        server_from_snapshot = self._boot_image(snapshot_image_id)

        # check the existence of the timestamp file in the second instance
        if self.config.compute.use_floatingip_for_ssh:
            fip_for_snapshot = self._create_floating_ip()
            self._set_floating_ip_to_server(server_from_snapshot,
                                            fip_for_snapshot)
            self._check_timestamp(fip_for_snapshot.ip)
        else:
            self._check_timestamp(server_from_snapshot)
