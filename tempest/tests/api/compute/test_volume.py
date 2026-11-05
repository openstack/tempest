# Copyright 2026 Adam Harwell
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

from unittest import mock

from tempest.api.compute.admin import test_volume
from tempest.tests import base


class TestCustomImage(base.TestCase):
    def setUp(self):
        super().setUp()
        self.patchobject(test_volume, 'CONF').compute.image_ref = 'source'
        self.fixture = mock.Mock()
        self.client = self.fixture.admin_image_client
        self.fixture.reader_image_client.show_image.return_value = {
            'container_format': 'bare', 'disk_format': 'raw',
            'min_disk': 1, 'min_ram': 64, 'kernel_id': 'kernel',
            'ramdisk_id': 'ramdisk'}
        self.client.create_image.return_value = {'id': 'destination'}
        self.response = self.client.show_image_file.return_value

    def create_image(self):
        test_class = test_volume.BaseAttachSCSIVolumeTest
        return test_class._create_image_with_custom_property(
            self.fixture, hw_scsi_model='virtio-scsi')

    def assert_cleanup_registered(self):
        self.fixture.addCleanup.assert_has_calls([
            mock.call(self.fixture.reader_image_client.
                      wait_for_resource_deletion, 'destination'),
            mock.call(self.client.delete_image, 'destination')])

    def test_download_opens_after_destination_is_created(self):
        # Do not keep a download unread while another API request runs:
        # the image server can time out writing that response.
        def open_stream(*args, **kwargs):
            self.client.create_image.assert_called_once_with(
                container_format='bare', disk_format='raw', min_disk=1,
                min_ram=64, visibility='public', kernel_id='kernel',
                ramdisk_id='ramdisk', hw_scsi_model='virtio-scsi')
            self.assert_cleanup_registered()
            return self.response

        self.client.show_image_file.side_effect = open_stream
        self.assertEqual('destination', self.create_image())
        self.client.show_image_file.assert_called_once_with(
            'source', chunked=True)
        self.client.store_image_file.assert_called_once_with(
            'destination', self.response)
        self.response.release_conn.assert_called_once_with()

    def test_create_failure_does_not_open_download(self):
        self.client.create_image.side_effect = RuntimeError('create failed')
        self.assertRaisesRegex(
            RuntimeError, 'create failed', self.create_image)
        self.client.show_image_file.assert_not_called()
        self.client.store_image_file.assert_not_called()
        self.fixture.addCleanup.assert_not_called()

    def test_download_failure_keeps_destination_cleanup(self):
        self.client.show_image_file.side_effect = RuntimeError(
            'download failed')
        self.assertRaisesRegex(
            RuntimeError, 'download failed', self.create_image)
        self.assert_cleanup_registered()
        self.client.store_image_file.assert_not_called()
        self.response.release_conn.assert_not_called()

    def test_upload_failure_releases_download(self):
        self.client.store_image_file.side_effect = RuntimeError(
            'upload failed')
        self.assertRaisesRegex(
            RuntimeError, 'upload failed', self.create_image)
        self.assert_cleanup_registered()
        self.response.release_conn.assert_called_once_with()
