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

from unittest import mock

from oslo_utils import uuidutils

from tempest.api.compute import base as compute_base
from tempest.common import waiters
from tempest import exceptions
from tempest.lib import exceptions as lib_exc
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
        cleanup_path = 'tempest.test.BaseTestCase.addClassResourceCleanup'
        with mock.patch(cleanup_path) as mock_cleanup:
            image = compute_base.BaseV2ComputeTest.create_image_from_server(
                mock.sentinel.server_id, name='fake-snapshot-name')
        self.assertEqual(fake_image, image)
        # make our assertions
        compute_images_client.create_image.assert_called_once_with(
            mock.sentinel.server_id, name='fake-snapshot-name')
        mock_cleanup.assert_called_once()
        self.assertIn(image_id, mock_cleanup.call_args[0])

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         servers_client=mock.DEFAULT,
                         images=[], create=True)
    @mock.patch.object(waiters, 'wait_for_image_status')
    @mock.patch.object(waiters, 'wait_for_server_status')
    def test_create_image_from_server_wait_until_active(self,
                                                        wait_for_server_status,
                                                        wait_for_image_status,
                                                        servers_client,
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
        wait_for_server_status.assert_called_once_with(
            servers_client, mock.sentinel.server_id, 'ACTIVE')
        compute_images_client.show_image.assert_called_once_with(image_id)

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         servers_client=mock.DEFAULT,
                         images=[], create=True)
    @mock.patch.object(waiters, 'wait_for_image_status')
    @mock.patch.object(waiters, 'wait_for_server_status')
    def test_create_image_from_server_wait_until_active_no_server_wait(
            self, wait_for_server_status, wait_for_image_status,
            servers_client, compute_images_client):
        """Tests create_image_from_server with wait_until='ACTIVE' kwarg."""
        # setup mocks
        image_id = uuidutils.generate_uuid()
        fake_image = mock.Mock(response={'location': image_id})
        compute_images_client.create_image.return_value = fake_image
        compute_images_client.show_image.return_value = (
            {'image': fake_image})
        # call the utility method
        image = compute_base.BaseV2ComputeTest.create_image_from_server(
            mock.sentinel.server_id, wait_until='ACTIVE',
            wait_for_server=False)
        self.assertEqual(fake_image, image)
        # make our assertions
        wait_for_image_status.assert_called_once_with(
            compute_images_client, image_id, 'ACTIVE')
        self.assertEqual(0, wait_for_server_status.call_count)
        compute_images_client.show_image.assert_called_once_with(image_id)

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         servers_client=mock.DEFAULT,
                         images=[], create=True)
    @mock.patch.object(waiters, 'wait_for_image_status',
                       side_effect=lib_exc.NotFound)
    def _test_create_image_from_server_wait_until_active_not_found(
            self, wait_for_image_status, compute_images_client,
            servers_client, fault=None):
        # setup mocks
        image_id = uuidutils.generate_uuid()
        fake_image = mock.Mock(response={'location': image_id})
        compute_images_client.create_image.return_value = fake_image
        fake_server = {'id': mock.sentinel.server_id}
        if fault:
            fake_server['fault'] = fault
        servers_client.show_server.return_value = {'server': fake_server}
        # call the utility method
        ex = self.assertRaises(
            exceptions.SnapshotNotFoundException,
            compute_base.BaseV2ComputeTest.create_image_from_server,
            mock.sentinel.server_id, wait_until='active')
        # make our assertions
        if fault:
            self.assertIn(fault, str(ex))
        else:
            self.assertNotIn(fault, str(ex))
        if compute_base.BaseV2ComputeTest.is_requested_microversion_compatible(
            '2.35'):
            status = 'ACTIVE'
        else:
            status = 'active'
        wait_for_image_status.assert_called_once_with(
            compute_images_client, image_id, status)
        servers_client.show_server.assert_called_once_with(
            mock.sentinel.server_id)

    def test_create_image_from_server_wait_until_active_not_found_no_fault(
            self):
        # Tests create_image_from_server with wait_until='active' kwarg and
        # the a 404 is raised while waiting for the image status to change. In
        # this test the server does not have a fault associated with it.
        self._test_create_image_from_server_wait_until_active_not_found()

    def test_create_image_from_server_wait_until_active_not_found_with_fault(
            self):
        # Tests create_image_from_server with wait_until='active' kwarg and
        # the a 404 is raised while waiting for the image status to change. In
        # this test the server has a fault associated with it.
        self._test_create_image_from_server_wait_until_active_not_found(
            fault='Lost connection to hypervisor!')

    @mock.patch.multiple(compute_base.BaseV2ComputeTest,
                         compute_images_client=mock.DEFAULT,
                         images=[], create=True)
    @mock.patch.object(waiters, 'wait_for_image_status',
                       side_effect=lib_exc.NotFound)
    def test_create_image_from_server_wait_until_saving_not_found(
            self, wait_for_image_status, compute_images_client):
        # Tests create_image_from_server with wait_until='SAVING' kwarg and
        # the a 404 is raised while waiting for the image status to change. In
        # this case we do not get the server details and just re-raise the 404.
        # setup mocks
        image_id = uuidutils.generate_uuid()
        fake_image = mock.Mock(response={'location': image_id})
        compute_images_client.create_image.return_value = fake_image
        # call the utility method
        self.assertRaises(
            lib_exc.NotFound,
            compute_base.BaseV2ComputeTest.create_image_from_server,
            mock.sentinel.server_id, wait_until='SAVING')
        # make our assertions
        wait_for_image_status.assert_called_once_with(
            compute_images_client, image_id, 'SAVING')

    def _test_version_compatible(self, max_version, expected=True):
        actual = (compute_base.BaseV2ComputeTest.
                  is_requested_microversion_compatible(max_version))
        self.assertEqual(expected, actual)

    def test_check_lower_version(self):
        compute_base.BaseV2ComputeTest.request_microversion = '2.8'
        self._test_version_compatible('2.40')

    def test_check_euqal_version(self):
        compute_base.BaseV2ComputeTest.request_microversion = '2.40'
        self._test_version_compatible('2.40')

    def test_check_higher_version(self):
        compute_base.BaseV2ComputeTest.request_microversion = '2.41'
        self._test_version_compatible('2.40', expected=False)
