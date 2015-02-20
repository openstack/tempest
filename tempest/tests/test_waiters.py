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
from tempest.tests import base


class TestImageWaiters(base.TestCase):
    def setUp(self):
        super(TestImageWaiters, self).setUp()
        self.client = mock.MagicMock()
        self.client.build_timeout = 1
        self.client.build_interval = 1

    def test_wait_for_image_status(self):
        self.client.get_image.return_value = ({'status': 'active'})
        start_time = int(time.time())
        waiters.wait_for_image_status(self.client, 'fake_image_id', 'active')
        end_time = int(time.time())
        # Ensure waiter returns before build_timeout
        self.assertTrue((end_time - start_time) < 10)

    def test_wait_for_image_status_timeout(self):
        self.client.get_image.return_value = ({'status': 'saving'})
        self.assertRaises(exceptions.TimeoutException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')

    def test_wait_for_image_status_error_on_image_create(self):
        self.client.get_image.return_value = ({'status': 'ERROR'})
        self.assertRaises(exceptions.AddImageException,
                          waiters.wait_for_image_status,
                          self.client, 'fake_image_id', 'active')
