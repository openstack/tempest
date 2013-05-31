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

import logging

from tempest.common.utils.data_utils import rand_name
from tempest.common.utils.linux.remote_client import RemoteClient
from tempest.scenario import manager


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

    def _wait_for_volume_status(self, status):
        volume_id = self.volume.id
        self.status_timeout(
            self.volume_client.volumes, volume_id, status)

    def _image_create(self, name, fmt, path, properties={}):
        name = rand_name('%s-' % name)
        image_file = open(path, 'rb')
        self.addCleanup(image_file.close)
        params = {
            'name': name,
            'container_format': fmt,
            'disk_format': fmt,
            'is_public': 'True',
        }
        params.update(properties)
        image = self.image_client.images.create(**params)
        self.addCleanup(self.image_client.images.delete, image)
        self.assertEqual("queued", image.status)
        image.update(data=image_file)
        return image.id

    def glance_image_create(self):
        aki_img_path = self.config.scenario.img_dir + "/" + \
            self.config.scenario.aki_img_file
        ari_img_path = self.config.scenario.img_dir + "/" + \
            self.config.scenario.ari_img_file
        ami_img_path = self.config.scenario.img_dir + "/" + \
            self.config.scenario.ami_img_file
        LOG.debug("paths: ami: %s, ari: %s, aki: %s"
                  % (ami_img_path, ari_img_path, aki_img_path))
        kernel_id = self._image_create('scenario-aki', 'aki', aki_img_path)
        ramdisk_id = self._image_create('scenario-ari', 'ari', ari_img_path)
        properties = {
            'properties': {'kernel_id': kernel_id, 'ramdisk_id': ramdisk_id}
        }
        self.image = self._image_create('scenario-ami', 'ami',
                                        path=ami_img_path,
                                        properties=properties)

    def nova_keypair_add(self):
        name = rand_name('scenario-keypair-')

        self.keypair = self.compute_client.keypairs.create(name=name)
        self.addCleanup(self.compute_client.keypairs.delete, self.keypair)
        self.assertEqual(name, self.keypair.name)

    def nova_boot(self):
        name = rand_name('scenario-server-')
        client = self.compute_client
        flavor_id = self.config.compute.flavor_ref
        self.server = client.servers.create(name=name, image=self.image,
                                            flavor=flavor_id,
                                            key_name=self.keypair.name)
        self.addCleanup(self.compute_client.servers.delete, self.server)
        self.assertEqual(name, self.server.name)
        self._wait_for_server_status('ACTIVE')

    def nova_list(self):
        servers = self.compute_client.servers.list()
        LOG.debug("server_list:%s" % servers)
        self.assertTrue(self.server in servers)

    def nova_show(self):
        got_server = self.compute_client.servers.get(self.server)
        LOG.debug("got server:%s" % got_server)
        self.assertEqual(self.server, got_server)

    def cinder_create(self):
        name = rand_name('scenario-volume-')
        LOG.debug("volume display-name:%s" % name)
        self.volume = self.volume_client.volumes.create(size=1,
                                                        display_name=name)
        LOG.debug("volume created:%s" % self.volume.display_name)
        self._wait_for_volume_status('available')

        self.addCleanup(self.volume_client.volumes.delete, self.volume)
        self.assertEqual(name, self.volume.display_name)

    def cinder_list(self):
        volumes = self.volume_client.volumes.list()
        self.assertTrue(self.volume in volumes)

    def cinder_show(self):
        volume = self.volume_client.volumes.get(self.volume.id)
        self.assertEqual(self.volume, volume)

    def nova_volume_attach(self):
        attach_volume_client = self.compute_client.volumes.create_server_volume
        volume = attach_volume_client(self.server.id,
                                      self.volume.id,
                                      '/dev/vdb')
        self.assertEqual(self.volume.id, volume.id)
        self._wait_for_volume_status('in-use')

    def nova_reboot(self):
        self.server.reboot()
        self._wait_for_server_status('ACTIVE')

    def nova_floating_ip_create(self):
        self.floating_ip = self.compute_client.floating_ips.create()
        self.addCleanup(self.floating_ip.delete)

    def nova_floating_ip_add(self):
        self.server.add_floating_ip(self.floating_ip)

    def nova_security_group_rule_create(self):
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

    def ssh_to_server(self):
        username = self.config.scenario.ssh_user
        self.linux_client = RemoteClient(self.floating_ip.ip,
                                         username,
                                         pkey=self.keypair.private_key)

    def check_partitions(self):
        partitions = self.linux_client.get_partitions()
        self.assertEqual(1, partitions.count('vdb'))

    def nova_volume_detach(self):
        detach_volume_client = self.compute_client.volumes.delete_server_volume
        detach_volume_client(self.server.id, self.volume.id)
        self._wait_for_volume_status('available')

        volume = self.volume_client.volumes.get(self.volume.id)
        self.assertEqual('available', volume.status)

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
        self.cinder_show()
        self.nova_reboot()

        self.nova_floating_ip_create()
        self.nova_floating_ip_add()
        self.nova_security_group_rule_create()
        self.ssh_to_server()
        self.check_partitions()

        self.nova_volume_detach()
