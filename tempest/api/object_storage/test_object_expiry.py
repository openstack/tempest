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
from tempest_lib import exceptions as lib_exc
import time

from tempest.api.object_storage import base
from tempest import test


class ObjectExpiryTest(base.BaseObjectTest):
    @classmethod
    def resource_setup(cls):
        super(ObjectExpiryTest, cls).resource_setup()
        cls.container_name = data_utils.rand_name(name='TestContainer')
        cls.container_client.create_container(cls.container_name)

    def setUp(self):
        super(ObjectExpiryTest, self).setUp()
        # create object
        self.object_name = data_utils.rand_name(name='TestObject')
        resp, _ = self.object_client.create_object(self.container_name,
                                                   self.object_name, '')

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers([cls.container_name])
        super(ObjectExpiryTest, cls).resource_cleanup()

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
        self.assertHeaders(resp, 'Object', 'HEAD')
        self.assertIn('x-delete-at', resp)
        # we want to ensure that we will sleep long enough for things to
        # actually expire, so figure out how many secs in the future that is.
        sleepy_time = int(resp['x-delete-at']) - int(time.time())

        resp, body = self.object_client.get_object(self.container_name,
                                                   self.object_name)
        self.assertHeaders(resp, 'Object', 'GET')
        self.assertIn('x-delete-at', resp)

        # add a couple of seconds for safety.
        time.sleep(sleepy_time + 3)

        # object should not be there anymore
        self.assertRaises(lib_exc.NotFound, self.object_client.get_object,
                          self.container_name, self.object_name)

    @test.attr(type='gate')
    @test.idempotent_id('fb024a42-37f3-4ba5-9684-4f40a7910b41')
    def test_get_object_after_expiry_time(self):
        # the 10s is important, because the get calls can take 3s each
        # some times
        metadata = {'X-Delete-After': '10'}
        self._test_object_expiry(metadata)

    @test.attr(type='gate')
    @test.idempotent_id('e592f18d-679c-48fe-9e36-4be5f47102c5')
    def test_get_object_at_expiry_time(self):
        metadata = {'X-Delete-At': str(int(time.time()) + 10)}
        self._test_object_expiry(metadata)
