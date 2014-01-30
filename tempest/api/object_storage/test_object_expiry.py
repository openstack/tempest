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

import time

from tempest.api.object_storage import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class ObjectExpiryTest(base.BaseObjectTest):
    @classmethod
    def setUpClass(cls):
        super(ObjectExpiryTest, cls).setUpClass()
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

    def setUp(self):
        super(ObjectExpiryTest, self).setUp()
        # create object
        self.object_name = data_utils.rand_name(name='TestObject')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   self.object_name, '')

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers([cls.container_name])
        super(ObjectExpiryTest, cls).tearDownClass()

    def _test_object_expiry(self, metadata):
        # update object metadata
        resp, _ = \
            self.object_client.update_object_metadata(self.container_name,
                                                      self.object_name,
                                                      metadata,
                                                      metadata_prefix='')
        # verify object metadata
        resp, _ = \
            self.object_client.list_object_metadata(self.container_name,
                                                    self.object_name)
        self.assertEqual(resp['status'], '200')
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertIn('x-delete-at', resp)
        resp, body = self.object_client.get_object(self.container_name,
                                                   self.object_name)
        self.assertEqual(resp['status'], '200')
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertIn('x-delete-at', resp)

        # sleep for over 5 seconds, so that object expires
        time.sleep(5)

        # object should not be there anymore
        self.assertRaises(exceptions.NotFound, self.object_client.get_object,
                          self.container_name, self.object_name)

    @attr(type='gate')
    def test_get_object_after_expiry_time(self):
        metadata = {'X-Delete-After': '3'}
        self._test_object_expiry(metadata)

    @attr(type='gate')
    def test_get_object_at_expiry_time(self):
        metadata = {'X-Delete-At': str(int(time.time()) + 3)}
        self._test_object_expiry(metadata)
