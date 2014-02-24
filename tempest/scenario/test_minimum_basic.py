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

from tempest.common import debug
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import services

CONF = config.CONF

LOG = logging.getLogger(__name__)


class TestMinimumBasicScenario(manager.OfficialClientTest):

    """
    This is a basic minimum scenario test.

    This test below:
    * across the multiple components
    * as a regular user
    * with and without optional parameters
    * check command outputs

    """

    def _wait_for_server_status(self, status):
        server_id = self.server.id
        self.status_timeout(
            self.compute_client.servers, server_id, status)

    def nova_keypair_add(self):
        self.keypair = self.create_keypair()

    def nova_boot(self):
        create_kwargs = {'key_name': self.keypair.name}
        self.server = self.create_server(image=self.image,
                                         create_kwargs=create_kwargs)

    def nova_list(self):
        servers = self.compute_client.servers.list()
        LOG.debug("server_list:%s" % servers)
        self.assertIn(self.server, servers)

    def nova_show(self):
        got_server = self.compute_client.servers.get(self.server)
        LOG.debug("got server:%s" % got_server)
        self.assertEqual(self.server, got_server)

    def cinder_create(self):
        self.volume = self.create_volume()

    def cinder_list(self):
        volumes = self.volume_client.volumes.list()
        self.assertIn(self.volume, volumes)

    def cinder_show(self):
        volume = self.volume_client.volumes.get(self.volume.id)
        self.assertEqual(self.volume, volume)

    def nova_volume_attach(self):
        attach_volume_client = self.compute_client.volumes.create_server_volume
        volume = attach_volume_client(self.server.id,
                                      self.volume.id,
                                      '/dev/vdb')
        self.assertEqual(self.volume.id, volume.id)
        self.wait_for_volume_status('in-use')

    def nova_reboot(self):
        self.server.reboot()
        self._wait_for_server_status('ACTIVE')

    def nova_floating_ip_create(self):
        self.floating_ip = self.compute_client.floating_ips.create()
        self.addCleanup(self.floating_ip.delete)

    def nova_floating_ip_add(self):
        self.server.add_floating_ip(self.floating_ip)

    def ssh_to_server(self):
        try:
            self.linux_client = self.get_remote_client(self.floating_ip.ip)
            self.linux_client.validate_authentication()
        except Exception:
            LOG.exception('ssh to server failed')
            self._log_console_output()
            debug.log_ip_ns()
            raise

    def check_partitions(self):
        partitions = self.linux_client.get_partitions()
        self.assertEqual(1, partitions.count('vdb'))

    def nova_volume_detach(self):
        detach_volume_client = self.compute_client.volumes.delete_server_volume
        detach_volume_client(self.server.id, self.volume.id)
        self.wait_for_volume_status('available')

        volume = self.volume_client.volumes.get(self.volume.id)
        self.assertEqual('available', volume.status)

    @services('compute', 'volume', 'image', 'network')
    def test_minimum_basic_scenario(self):
        self.glance_image_create()
        self.nova_keypair_add()
        self.nova_boot()
        self.nova_list()
        self.nova_show()
        self.cinder_create()
        self.cinder_list()
        self.cinder_show()
        self.nova_volume_attach()
        self.addCleanup(self.nova_volume_detach)
        self.cinder_show()

        self.nova_floating_ip_create()
        self.nova_floating_ip_add()
        self._create_loginable_secgroup_rule_nova()
        self.ssh_to_server()
        self.nova_reboot()
        self.ssh_to_server()
        self.check_partitions()
