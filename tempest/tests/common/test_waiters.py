# Copyright 2014 IBM Corp.
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

import time

import mock

from tempest.common import waiters
from tempest import exceptions
from tempest.services.volume.base import base_volumes_client
from tempest.tests import base
import tempest.tests.utils as utils


class TestImageWaiters(base.TestCase):
    def setUp(self):
        super(TestImageWaiters, self).setUp()
        self.client = mock.MagicMock()
        self.client.build_timeout = 1
        self.client.build_interval = 1

    def test_wait_for_image_status(self):
        self.client.show_image.return_value = ({'status': 'active'})
        start_time = int(time.time())
        waiters.wait_for_image_status(self.client, 'fake_image_id', 'active')
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 10)

    @mock.patch('time.sleep')
    def test_wait_for_image_status_timeout(self, mock_sleep):
        time_mock = self.patch('time.time')
        time_mock.side_effect = utils.generate_timeout_series(1)

        self.client.show_image.return_value = ({'status': 'saving'})
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')
        mock_sleep.assert_called_once_with(1)

    @mock.patch('time.sleep')
    def test_wait_for_image_status_error_on_image_create(self, mock_sleep):
        self.client.show_image.return_value = ({'status': 'ERROR'})
        self.assertRaises(exceptions.AddImageException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')
        mock_sleep.assert_called_once_with(1)

    @mock.patch.object(time, 'sleep')
    def test_wait_for_volume_status_error_restoring(self, mock_sleep):
        # Tests that the wait method raises VolumeRestoreErrorException if
        # the volume status is 'error_restoring'.
        client = mock.Mock(spec=base_volumes_client.BaseVolumesClient,
                           build_interval=1)
        volume1 = {'volume': {'status': 'restoring-backup'}}
        volume2 = {'volume': {'status': 'error_restoring'}}
        mock_show = mock.Mock(side_effect=(volume1, volume2))
        client.show_volume = mock_show
        volume_id = '7532b91e-aa0a-4e06-b3e5-20c0c5ee1caa'
        self.assertRaises(exceptions.VolumeRestoreErrorException,
                          waiters.wait_for_volume_status,
                          client, volume_id, 'available')
        mock_show.assert_has_calls([mock.call(volume_id),
                                    mock.call(volume_id)])
        mock_sleep.assert_called_once_with(1)
