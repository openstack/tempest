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
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib import exceptions
from tempest import test
import testtools

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
        cls.server = cls.create_server(
            name=srv_name,
            wait_until='ACTIVE')

        # Create a test shared volume for attach/detach tests
        cls.volume = cls.create_volume()
        waiters.wait_for_volume_status(cls.client,
                                       cls.volume['id'], 'available')

    @classmethod
    def resource_cleanup(cls):
        # Delete the test instance
        cls.servers_client.delete_server(cls.server['id'])
        waiters.wait_for_server_termination(cls.servers_client,
                                            cls.server['id'])

        super(VolumesV2ActionsTest, cls).resource_cleanup()

    @test.idempotent_id('fff42874-7db5-4487-a8e1-ddda5fb5288d')
    @test.stresstest(class_setup_per='process')
    @test.attr(type='smoke')
    @test.services('compute')
    def test_attach_detach_volume_to_instance(self):
        # Volume is attached and detached successfully from an instance
        self.client.attach_volume(self.volume['id'],
                                  instance_uuid=self.server['id'],
                                  mountpoint='/dev/%s' %
                                             CONF.compute.volume_device_name)
        waiters.wait_for_volume_status(self.client,
                                       self.volume['id'], 'in-use')
        self.client.detach_volume(self.volume['id'])
        waiters.wait_for_volume_status(self.client,
                                       self.volume['id'], 'available')

    @test.idempotent_id('63e21b4c-0a0c-41f6-bfc3-7c2816815599')
    @testtools.skipUnless(CONF.volume_feature_enabled.bootable,
                          'Update bootable status of a volume is not enabled.')
    def test_volume_bootable(self):
        # Verify that a volume bootable flag is retrieved
        for bool_bootable in [True, False]:
            self.client.set_bootable_volume(self.volume['id'],
                                            bootable=bool_bootable)
            fetched_volume = self.client.show_volume(
                self.volume['id'])['volume']
            # Get Volume information
            bool_flag = self._is_true(fetched_volume['bootable'])
            self.assertEqual(bool_bootable, bool_flag)

    @test.idempotent_id('9516a2c8-9135-488c-8dd6-5677a7e5f371')
    @test.stresstest(class_setup_per='process')
    @test.services('compute')
    def test_get_volume_attachment(self):
        # Verify that a volume's attachment information is retrieved
        self.client.attach_volume(self.volume['id'],
                                  instance_uuid=self.server['id'],
                                  mountpoint='/dev/%s' %
                                             CONF.compute.volume_device_name)
        waiters.wait_for_volume_status(self.client,
                                       self.volume['id'], 'in-use')
        # NOTE(gfidente): added in reverse order because functions will be
        # called in reverse order to the order they are added (LIFO)
        self.addCleanup(waiters.wait_for_volume_status, self.client,
                        self.volume['id'],
                        'available')
        self.addCleanup(self.client.detach_volume, self.volume['id'])
        volume = self.client.show_volume(self.volume['id'])['volume']
        self.assertIn('attachments', volume)
        attachment = self.client.get_attachment_from_volume(volume)
        self.assertEqual('/dev/%s' %
                         CONF.compute.volume_device_name,
                         attachment['device'])
        self.assertEqual(self.server['id'], attachment['server_id'])
        self.assertEqual(self.volume['id'], attachment['id'])
        self.assertEqual(self.volume['id'], attachment['volume_id'])

    @test.idempotent_id('d8f1ca95-3d5b-44a3-b8ca-909691c9532d')
    @test.services('image')
    def test_volume_upload(self):
        # NOTE(gfidente): the volume uploaded in Glance comes from setUpClass,
        # it is shared with the other tests. After it is uploaded in Glance,
        # there is no way to delete it from Cinder, so we delete it from Glance
        # using the Glance image_client and from Cinder via tearDownClass.
        image_name = data_utils.rand_name('Image')
        body = self.client.upload_volume(
            self.volume['id'], image_name=image_name,
            disk_format=CONF.volume.disk_format)['os-volume_upload_image']
        image_id = body["image_id"]
        self.addCleanup(self._cleanup_image, image_id)
        self.image_client.wait_for_image_status(image_id, 'active')
        waiters.wait_for_volume_status(self.client,
                                       self.volume['id'], 'available')

    def _cleanup_image(self, image_id):
        # Ignores the image deletion
        # in the case that image wasn't created in the first place
        try:
            self.image_client.delete_image(image_id)
        except exceptions.NotFound:
            pass

    @test.idempotent_id('92c4ef64-51b2-40c0-9f7e-4749fbaaba33')
    def test_reserve_unreserve_volume(self):
        # Mark volume as reserved.
        body = self.client.reserve_volume(self.volume['id'])
        # To get the volume info
        body = self.client.show_volume(self.volume['id'])['volume']
        self.assertIn('attaching', body['status'])
        # Unmark volume as reserved.
        body = self.client.unreserve_volume(self.volume['id'])
        # To get the volume info
        body = self.client.show_volume(self.volume['id'])['volume']
        self.assertIn('available', body['status'])

    def _is_true(self, val):
        return val in ['true', 'True', True]

    @test.idempotent_id('fff74e1e-5bd3-4b33-9ea9-24c103bc3f59')
    def test_volume_readonly_update(self):
        # Update volume readonly true
        readonly = True
        self.client.update_volume_readonly(self.volume['id'],
                                           readonly=readonly)
        # Get Volume information
        fetched_volume = self.client.show_volume(self.volume['id'])['volume']
        bool_flag = self._is_true(fetched_volume['metadata']['readonly'])
        self.assertEqual(True, bool_flag)

        # Update volume readonly false
        readonly = False
        self.client.update_volume_readonly(self.volume['id'],
                                           readonly=readonly)

        # Get Volume information
        fetched_volume = self.client.show_volume(self.volume['id'])['volume']
        bool_flag = self._is_true(fetched_volume['metadata']['readonly'])
        self.assertEqual(False, bool_flag)


class VolumesV1ActionsTest(VolumesV2ActionsTest):
    _api_version = 1
