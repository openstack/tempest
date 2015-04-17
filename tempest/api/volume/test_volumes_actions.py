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

from tempest_lib.common.utils import data_utils

from tempest.api.volume import base
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesV2ActionsTest(base.BaseVolumeTest):

    @classmethod
    def setup_clients(cls):
        super(VolumesV2ActionsTest, cls).setup_clients()
        cls.client = cls.volumes_client
        cls.image_client = cls.os.image_client

    @classmethod
    def resource_setup(cls):
        super(VolumesV2ActionsTest, cls).resource_setup()

        # Create a test shared instance
        srv_name = data_utils.rand_name(cls.__name__ + '-Instance')
        cls.server = cls.create_server(srv_name)
        cls.servers_client.wait_for_server_status(cls.server['id'], 'ACTIVE')

        # Create a test shared volume for attach/detach tests
        cls.volume = cls.create_volume()
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')

    def _delete_image_with_wait(self, image_id):
        self.image_client.delete_image(image_id)
        self.image_client.wait_for_resource_deletion(image_id)

    @classmethod
    def resource_cleanup(cls):
        # Delete the test instance
        cls.servers_client.delete_server(cls.server['id'])
        cls.servers_client.wait_for_server_termination(cls.server['id'])

        super(VolumesV2ActionsTest, cls).resource_cleanup()

    @test.idempotent_id('fff42874-7db5-4487-a8e1-ddda5fb5288d')
    @test.stresstest(class_setup_per='process')
    @test.attr(type='smoke')
    @test.services('compute')
    def test_attach_detach_volume_to_instance(self):
        # Volume is attached and detached successfully from an instance
        mountpoint = '/dev/vdc'
        self.client.attach_volume(self.volume['id'],
                                  self.server['id'],
                                  mountpoint)
        self.client.wait_for_volume_status(self.volume['id'], 'in-use')
        self.client.detach_volume(self.volume['id'])
        self.client.wait_for_volume_status(self.volume['id'], 'available')

    @test.idempotent_id('9516a2c8-9135-488c-8dd6-5677a7e5f371')
    @test.stresstest(class_setup_per='process')
    @test.attr(type='gate')
    @test.services('compute')
    def test_get_volume_attachment(self):
        # Verify that a volume's attachment information is retrieved
        mountpoint = '/dev/vdc'
        self.client.attach_volume(self.volume['id'],
                                  self.server['id'],
                                  mountpoint)
        self.client.wait_for_volume_status(self.volume['id'], 'in-use')
        # NOTE(gfidente): added in reverse order because functions will be
        # called in reverse order to the order they are added (LIFO)
        self.addCleanup(self.client.wait_for_volume_status,
                        self.volume['id'],
                        'available')
        self.addCleanup(self.client.detach_volume, self.volume['id'])
        volume = self.client.show_volume(self.volume['id'])
        self.assertIn('attachments', volume)
        attachment = self.client.get_attachment_from_volume(volume)
        self.assertEqual(mountpoint, attachment['device'])
        self.assertEqual(self.server['id'], attachment['server_id'])
        self.assertEqual(self.volume['id'], attachment['id'])
        self.assertEqual(self.volume['id'], attachment['volume_id'])

    @test.attr(type='gate')
    @test.idempotent_id('d8f1ca95-3d5b-44a3-b8ca-909691c9532d')
    @test.services('image')
    def test_volume_upload(self):
        # NOTE(gfidente): the volume uploaded in Glance comes from setUpClass,
        # it is shared with the other tests. After it is uploaded in Glance,
        # there is no way to delete it from Cinder, so we delete it from Glance
        # using the Glance image_client and from Cinder via tearDownClass.
        image_name = data_utils.rand_name('Image')
        body = self.client.upload_volume(self.volume['id'],
                                         image_name,
                                         CONF.volume.disk_format)
        image_id = body["image_id"]
        self.addCleanup(self.image_client.delete_image, image_id)
        self.image_client.wait_for_image_status(image_id, 'active')
        self.client.wait_for_volume_status(self.volume['id'], 'available')

    @test.attr(type='gate')
    @test.idempotent_id('92c4ef64-51b2-40c0-9f7e-4749fbaaba33')
    def test_reserve_unreserve_volume(self):
        # Mark volume as reserved.
        body = self.client.reserve_volume(self.volume['id'])
        # To get the volume info
        body = self.client.show_volume(self.volume['id'])
        self.assertIn('attaching', body['status'])
        # Unmark volume as reserved.
        body = self.client.unreserve_volume(self.volume['id'])
        # To get the volume info
        body = self.client.show_volume(self.volume['id'])
        self.assertIn('available', body['status'])

    def _is_true(self, val):
        return val in ['true', 'True', True]

    @test.attr(type='gate')
    @test.idempotent_id('fff74e1e-5bd3-4b33-9ea9-24c103bc3f59')
    def test_volume_readonly_update(self):
        # Update volume readonly true
        readonly = True
        self.client.update_volume_readonly(self.volume['id'],
                                           readonly)
        # Get Volume information
        fetched_volume = self.client.show_volume(self.volume['id'])
        bool_flag = self._is_true(fetched_volume['metadata']['readonly'])
        self.assertEqual(True, bool_flag)

        # Update volume readonly false
        readonly = False
        self.client.update_volume_readonly(self.volume['id'], readonly)

        # Get Volume information
        fetched_volume = self.client.show_volume(self.volume['id'])
        bool_flag = self._is_true(fetched_volume['metadata']['readonly'])
        self.assertEqual(False, bool_flag)


class VolumesV1ActionsTest(VolumesV2ActionsTest):
    _api_version = 1
