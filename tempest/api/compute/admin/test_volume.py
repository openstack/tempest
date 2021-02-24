# Copyright 2020 Red Hat Inc.
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

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class BaseAttachSCSIVolumeTest(base.BaseV2ComputeAdminTest):
    """Base class for the admin volume tests in this module."""
    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(BaseAttachSCSIVolumeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(BaseAttachSCSIVolumeTest, cls).setup_credentials()

    def _create_image_with_custom_property(self, **kwargs):
        """Wrapper utility that returns the custom image.

        Creates a new image by downloading the default image's bits and
        uploading them to a new image. Any kwargs are set as image properties
        on the new image.

        :param return image_id: The UUID of the newly created image.
        """
        image = self.image_client.show_image(CONF.compute.image_ref)
        image_data = self.image_client.show_image_file(
            CONF.compute.image_ref).data
        image_file = io.BytesIO(image_data)
        create_dict = {
            'container_format': image['container_format'],
            'disk_format': image['disk_format'],
            'min_disk': image['min_disk'],
            'min_ram': image['min_ram'],
            'visibility': 'public',
        }
        create_dict.update(kwargs)
        new_image = self.image_client.create_image(**create_dict)
        self.addCleanup(self.image_client.wait_for_resource_deletion,
                        new_image['id'])
        self.addCleanup(self.image_client.delete_image, new_image['id'])
        self.image_client.store_image_file(new_image['id'], image_file)

        return new_image['id']


class AttachSCSIVolumeTestJSON(BaseAttachSCSIVolumeTest):
    """Test attaching scsi volume to server"""

    @decorators.idempotent_id('777e468f-17ca-4da4-b93d-b7dbf56c0494')
    def test_attach_scsi_disk_with_config_drive(self):
        """Test the attach/detach volume with config drive/scsi disk

        Enable the config drive, followed by booting an instance
        from an image with meta properties hw_cdrom: scsi and use
        virtio-scsi mode with further asserting list volume attachments
        in instance after attach and detach of the volume.
        """
        custom_img = self._create_image_with_custom_property(
            hw_scsi_model='virtio-scsi',
            hw_disk_bus='scsi',
            hw_cdrom_bus='scsi')
        server = self.create_test_server(image_id=custom_img,
                                         config_drive=True,
                                         wait_until='ACTIVE')

        # NOTE(lyarwood): self.create_test_server delete the server
        # at class level cleanup so add server cleanup to ensure that
        # the instance is deleted first before created image. This
        # avoids failures when using the rbd backend is used for both
        # Glance and Nova ephemeral storage. Also wait until server is
        # deleted otherwise image deletion can start before server is
        # deleted.
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(self.servers_client.delete_server, server['id'])

        volume = self.create_volume()
        attachment = self.attach_volume(server, volume)
        waiters.wait_for_volume_resource_status(
            self.volumes_client, attachment['volumeId'], 'in-use')
        volume_after_attach = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(volume_after_attach),
                         "Failed to attach volume")
        self.servers_client.detach_volume(
            server['id'], attachment['volumeId'])
        waiters.wait_for_volume_resource_status(
            self.volumes_client, attachment['volumeId'], 'available')
        waiters.wait_for_volume_attachment_remove_from_server(
            self.servers_client, server['id'], attachment['volumeId'])
