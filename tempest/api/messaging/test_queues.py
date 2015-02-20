# Copyright (c) 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from six import moves
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc
from testtools import matchers

from tempest.api.messaging import base
from tempest import test


LOG = logging.getLogger(__name__)


class TestQueues(base.BaseMessagingTest):

    @test.attr(type='smoke')
    @test.idempotent_id('9f1c4c72-80c5-4dac-acf3-188cef42e36c')
    def test_create_delete_queue(self):
        # Create & Delete Queue
        queue_name = data_utils.rand_name('test-')
        _, body = self.create_queue(queue_name)

        self.addCleanup(self.client.delete_queue, queue_name)
        # NOTE(gmann): create_queue returns response status code as 201
        # so specifically checking the expected empty response body as
        # this is not going to be checked in response_checker().
        self.assertEqual('', body)

        self.delete_queue(queue_name)
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_queue,
                          queue_name)


class TestManageQueue(base.BaseMessagingTest):

    @classmethod
    def resource_setup(cls):
        super(TestManageQueue, cls).resource_setup()
        cls.queues = list()
        for _ in moves.xrange(5):
            queue_name = data_utils.rand_name('Queues-Test')
            cls.queues.append(queue_name)
            # Create Queue
            cls.client.create_queue(queue_name)

    @test.attr(type='smoke')
    @test.idempotent_id('ccd3d69e-f156-4c5f-8a12-b4f24bee44e1')
    def test_check_queue_existence(self):
        # Checking Queue Existence
        for queue_name in self.queues:
            self.check_queue_exists(queue_name)

    @test.attr(type='smoke')
    @test.idempotent_id('e27634d8-9c8f-47d8-a677-655c47658d3e')
    def test_check_queue_head(self):
        # Checking Queue Existence by calling HEAD
        for queue_name in self.queues:
            self.check_queue_exists_head(queue_name)

    @test.attr(type='smoke')
    @test.idempotent_id('0a0feeca-7768-4303-806d-82bbbb796ad3')
    def test_list_queues(self):
        # Listing queues
        _, body = self.list_queues()
        self.assertEqual(len(body['queues']), len(self.queues))
        for item in body['queues']:
            self.assertIn(item['name'], self.queues)

    @test.attr(type='smoke')
    @test.idempotent_id('8fb66602-077d-49d6-ae1a-5f2091739178')
    def test_get_queue_stats(self):
        # Retrieve random queue
        queue_name = self.queues[data_utils.rand_int_id(0,
                                                        len(self.queues) - 1)]
        # Get Queue Stats for a newly created Queue
        _, body = self.get_queue_stats(queue_name)
        msgs = body['messages']
        for element in ('free', 'claimed', 'total'):
            self.assertEqual(0, msgs[element])
        for element in ('oldest', 'newest'):
            self.assertNotIn(element, msgs)

    @test.attr(type='smoke')
    @test.idempotent_id('0e2441e6-6593-4bdb-a3c0-20e66eeb3fff')
    def test_set_and_get_queue_metadata(self):
        # Retrieve random queue
        queue_name = self.queues[data_utils.rand_int_id(0,
                                                        len(self.queues) - 1)]
        # Check the Queue has no metadata
        _, body = self.get_queue_metadata(queue_name)
        self.assertThat(body, matchers.HasLength(0))
        # Create metadata
        key3 = [0, 1, 2, 3, 4]
        key2 = data_utils.rand_name('value')
        req_body1 = dict()
        req_body1[data_utils.rand_name('key3')] = key3
        req_body1[data_utils.rand_name('key2')] = key2
        req_body = dict()
        req_body[data_utils.rand_name('key1')] = req_body1
        # Set Queue Metadata
        self.set_queue_metadata(queue_name, req_body)

        # Get Queue Metadata
        _, body = self.get_queue_metadata(queue_name)
        self.assertThat(body, matchers.Equals(req_body))

    @classmethod
    def resource_cleanup(cls):
        for queue_name in cls.queues:
            cls.client.delete_queue(queue_name)
        super(TestManageQueue, cls).resource_cleanup()
