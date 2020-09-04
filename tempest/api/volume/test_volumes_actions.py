# Copyright 2012 OpenStack Foundation
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

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumesActionsTest(base.BaseVolumeTest):
    """Test volume actions"""

    create_default_network = True

    @classmethod
    def resource_setup(cls):
        super(VolumesActionsTest, cls).resource_setup()

        # Create a test shared volume for attach/detach tests
        cls.volume = cls.create_volume()

    @decorators.idempotent_id('fff42874-7db5-4487-a8e1-ddda5fb5288d')
    @decorators.attr(type='smoke')
    @utils.services('compute')
    def test_attach_detach_volume_to_instance(self):
        """Test attaching and detaching volume to instance"""
        # Create a server
        server = self.create_server()
        # Volume is attached and detached successfully from an instance
        self.volumes_client.attach_volume(self.volume['id'],
                                          instance_uuid=server['id'],
                                          mountpoint='/dev/%s' %
                                          CONF.compute.volume_device_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                self.volume['id'], 'in-use')
        self.volumes_client.detach_volume(self.volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                self.volume['id'], 'available')

    @decorators.idempotent_id('63e21b4c-0a0c-41f6-bfc3-7c2816815599')
    def test_volume_bootable(self):
        """Test setting and retrieving bootable flag of a volume"""
        for bool_bootable in [True, False]:
            self.volumes_client.set_bootable_volume(self.volume['id'],
                                                    bootable=bool_bootable)
            fetched_volume = self.volumes_client.show_volume(
                self.volume['id'])['volume']
            # Get Volume information
            # NOTE(masayukig): 'bootable' is "true" or "false" in the current
            # cinder implementation. So we need to cast boolean values to str
            # and make it lower to compare here.
            self.assertEqual(str(bool_bootable).lower(),
                             fetched_volume['bootable'])

    @decorators.idempotent_id('9516a2c8-9135-488c-8dd6-5677a7e5f371')
    @utils.services('compute')
    def test_get_volume_attachment(self):
        """Test getting volume attachments

        Attach a volume to a server, and then retrieve volume's attachments
        info.
        """
        # Create a server
        server = self.create_server()
        # Verify that a volume's attachment information is retrieved
        self.volumes_client.attach_volume(self.volume['id'],
                                          instance_uuid=server['id'],
                                          mountpoint='/dev/%s' %
                                          CONF.compute.volume_device_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                self.volume['id'],
                                                'in-use')
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.volumes_client,
                        self.volume['id'], 'available')
        self.addCleanup(self.volumes_client.detach_volume, self.volume['id'])
        volume = self.volumes_client.show_volume(self.volume['id'])['volume']
        attachment = volume['attachments'][0]

        self.assertEqual('/dev/%s' %
                         CONF.compute.volume_device_name,
                         attachment['device'])
        self.assertEqual(server['id'], attachment['server_id'])
        self.assertEqual(self.volume['id'], attachment['id'])
        self.assertEqual(self.volume['id'], attachment['volume_id'])

    @decorators.idempotent_id('d8f1ca95-3d5b-44a3-b8ca-909691c9532d')
    @utils.services('image')
    def test_volume_upload(self):
        """Test uploading volume to create an image"""
        # NOTE(gfidente): the volume uploaded in Glance comes from setUpClass,
        # it is shared with the other tests. After it is uploaded in Glance,
        # there is no way to delete it from Cinder, so we delete it from Glance
        # using the Glance images_client and from Cinder via tearDownClass.
        image_name = data_utils.rand_name(self.__class__.__name__ + '-Image')
        body = self.volumes_client.upload_volume(
            self.volume['id'], image_name=image_name,
            disk_format=CONF.volume.disk_format)['os-volume_upload_image']
        image_id = body["image_id"]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.images_client.delete_image,
                        image_id)
        waiters.wait_for_image_status(self.images_client, image_id, 'active')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                self.volume['id'], 'available')

        image_info = self.images_client.show_image(image_id)
        self.assertEqual(image_name, image_info['name'])
        self.assertEqual(CONF.volume.disk_format, image_info['disk_format'])

    @decorators.idempotent_id('92c4ef64-51b2-40c0-9f7e-4749fbaaba33')
    def test_reserve_unreserve_volume(self):
        """Test reserving and unreserving volume"""
        # Mark volume as reserved.
        self.volumes_client.reserve_volume(self.volume['id'])
        # To get the volume info
        body = self.volumes_client.show_volume(self.volume['id'])['volume']
        self.assertIn('attaching', body['status'])
        # Unmark volume as reserved.
        self.volumes_client.unreserve_volume(self.volume['id'])
        # To get the volume info
        body = self.volumes_client.show_volume(self.volume['id'])['volume']
        self.assertIn('available', body['status'])

    @decorators.idempotent_id('fff74e1e-5bd3-4b33-9ea9-24c103bc3f59')
    def test_volume_readonly_update(self):
        """Test updating and retrieve volume's readonly flag"""
        for readonly in [True, False]:
            # Update volume readonly
            self.volumes_client.update_volume_readonly(self.volume['id'],
                                                       readonly=readonly)
            # Get Volume information
            fetched_volume = self.volumes_client.show_volume(
                self.volume['id'])['volume']
            # NOTE(masayukig): 'readonly' is "True" or "False" in the current
            # cinder implementation. So we need to cast boolean values to str
            # to compare here.
            self.assertEqual(str(readonly),
                             fetched_volume['metadata']['readonly'])
