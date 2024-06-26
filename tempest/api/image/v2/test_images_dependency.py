# Copyright 2024 OpenStack Foundation
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

import io

from oslo_log import log as logging

from tempest.api.compute import base as compute_base
from tempest.api.image import base as image_base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ImageDependencyTests(image_base.BaseV2ImageTest,
                           compute_base.BaseV2ComputeTest,
                           manager.ScenarioTest):
    """Test image, instance, and snapshot dependency.

       The tests create image and remove the base image that other snapshots
       were depend on.In OpenStack, images and snapshots should be separate,
       but in some configurations like Glance with Ceph storage,
       there were cases where images couldn't be removed.
       This was fixed in glance store for RBD backend.

       * Dependency scenarios:
           - image > instance -> snapshot dependency

       NOTE: volume -> image dependencies tests are in cinder-tempest-plugin
    """

    @classmethod
    def skip_checks(cls):
        super(ImageDependencyTests, cls).skip_checks()
        if not CONF.volume_feature_enabled.enable_volume_image_dep_tests:
            skip_msg = (
                "%s Volume/image dependency tests "
                "not enabled" % (cls.__name__))
            raise cls.skipException(skip_msg)

    def _create_instance_snapshot(self, bfv=False):
        """Create instance from image and then snapshot the instance."""
        # Create image and store data to image
        source = 'volume' if bfv else 'image'
        image_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name='image-dependency-test')
        image = self.create_image(name=image_name,
                                  container_format='bare',
                                  disk_format='raw',
                                  visibility='private')
        file_content = data_utils.random_bytes()
        image_file = io.BytesIO(file_content)
        self.client.store_image_file(image['id'], image_file)
        waiters.wait_for_image_status(
            self.client, image['id'], 'active')
        if bfv:
            # Create instance
            instance = self.create_test_server(
                name='instance-depend-image',
                image_id=image['id'],
                volume_backed=True,
                wait_until='ACTIVE')
        else:
            # Create instance
            instance = self.create_test_server(
                name='instance-depend-image',
                image_id=image['id'],
                wait_until='ACTIVE')
        LOG.info("Instance from %s is created %s", source, instance)
        instance_observed = \
            self.servers_client.show_server(instance['id'])['server']
        # Create instance snapshot
        snapshot_instance = self.create_server_snapshot(
            server=instance_observed)
        LOG.info("Instance snapshot is created %s", snapshot_instance)
        return image['id'], snapshot_instance['id']

    @decorators.idempotent_id('d19b0731-e98e-4103-8b0e-02f651b8f586')
    @utils.services('compute')
    def test_nova_image_snapshot_dependency(self):
        """Test with image > instance > snapshot dependency.

        Create instance snapshot and check if we able to delete base
        image

        """
        base_image_id, snapshot_image_id = self._create_instance_snapshot()
        self.client.delete_image(base_image_id)
        self.client.wait_for_resource_deletion(base_image_id)
        images_list = self.client.list_images()['images']
        fetched_images_id = [img['id'] for img in images_list]
        self.assertNotIn(base_image_id, fetched_images_id)
        self.assertIn(snapshot_image_id, fetched_images_id)

    @utils.services('compute', 'volume')
    @decorators.idempotent_id('f0c8a35d-8f8f-443c-8bcb-85a9c0f87d19')
    def test_image_volume_server_snapshot_dependency(self):
        """Test with image > volume > instance > snapshot dependency.

        We are going to perform the following steps in the test:
        * Create image
        * Create a bootable volume from Image
        * Launch an instance from the bootable volume
        * Take snapshot of the instance -- which creates the volume snapshot
        * Delete the image.

        This will test the dependency chain of image -> volume -> snapshot.
        """
        base_image_id, snapshot_image_id = self._create_instance_snapshot(
            bfv=True)
        self.client.delete_image(base_image_id)
        self.client.wait_for_resource_deletion(base_image_id)
        images_list = self.client.list_images()['images']
        fetched_images_id = [img['id'] for img in images_list]
        self.assertNotIn(base_image_id, fetched_images_id)
        self.assertIn(snapshot_image_id, fetched_images_id)
