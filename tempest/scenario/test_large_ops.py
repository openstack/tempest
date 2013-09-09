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
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import services


LOG = logging.getLogger(__name__)


class TestLargeOpsScenario(manager.OfficialClientTest):

    """
    Test large operations.

    This test below:
    * Spin up multiple instances in one nova call
    * as a regular user
    * TODO: same thing for cinder

    """

    def _wait_for_server_status(self, status):
        for server in self.servers:
            self.status_timeout(
                self.compute_client.servers, server.id, status)

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

    def nova_boot(self):
        def delete(servers):
            [x.delete() for x in servers]

        name = rand_name('scenario-server-')
        client = self.compute_client
        flavor_id = self.config.compute.flavor_ref
        self.servers = client.servers.create(
            name=name, image=self.image,
            flavor=flavor_id,
            min_count=self.config.scenario.large_ops_number)
        # needed because of bug 1199788
        self.servers = [x for x in client.servers.list() if name in x.name]
        self.addCleanup(delete, self.servers)
        self._wait_for_server_status('ACTIVE')

    @services('compute', 'image')
    def test_large_ops_scenario(self):
        if self.config.scenario.large_ops_number < 1:
            return
        self.glance_image_create()
        self.nova_boot()
