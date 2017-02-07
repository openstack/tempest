# Copyright 2017 IBM Corp.
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

import mock

from oslo_utils import uuidutils

from tempest.api.compute import base as compute_base
from tempest.common import waiters
from tempest.tests import base


class TestBaseV2ComputeTest(base.TestCase):
    """Unit tests for utility functions in BaseV2ComputeTest."""

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         images=[], create=True)
    def test_create_image_from_server_no_wait(self, compute_images_client):
        """Tests create_image_from_server without the wait_until kwarg."""
        # setup mocks
        image_id = uuidutils.generate_uuid()
        fake_image = mock.Mock(response={'location': image_id})
        compute_images_client.create_image.return_value = fake_image
        # call the utility method
        image = compute_base.BaseV2ComputeTest.create_image_from_server(
            mock.sentinel.server_id, name='fake-snapshot-name')
        self.assertEqual(fake_image, image)
        # make our assertions
        compute_images_client.create_image.assert_called_once_with(
            mock.sentinel.server_id, name='fake-snapshot-name')
        self.assertEqual(1, len(compute_base.BaseV2ComputeTest.images))
        self.assertEqual(image_id, compute_base.BaseV2ComputeTest.images[0])

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         images=[], create=True)
    @mock.patch.object(waiters, 'wait_for_image_status')
    def test_create_image_from_server_wait_until_active(self,
                                                        wait_for_image_status,
                                                        compute_images_client):
        """Tests create_image_from_server with wait_until='ACTIVE' kwarg."""
        # setup mocks
        image_id = uuidutils.generate_uuid()
        fake_image = mock.Mock(response={'location': image_id})
        compute_images_client.create_image.return_value = fake_image
        compute_images_client.show_image.return_value = (
            {'image': fake_image})
        # call the utility method
        image = compute_base.BaseV2ComputeTest.create_image_from_server(
            mock.sentinel.server_id, wait_until='ACTIVE')
        self.assertEqual(fake_image, image)
        # make our assertions
        wait_for_image_status.assert_called_once_with(
            compute_images_client, image_id, 'ACTIVE')
        compute_images_client.show_image.assert_called_once_with(image_id)
