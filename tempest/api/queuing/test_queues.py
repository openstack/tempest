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
from testtools import matchers

from tempest.api.queuing import base
from tempest.common.utils import data_utils
from tempest import test


LOG = logging.getLogger(__name__)


class TestQueues(base.BaseQueuingTest):

    @test.attr(type='smoke')
    def test_create_queue(self):
        # Create Queue
        queue_name = data_utils.rand_name('test-')
        resp, body = self.create_queue(queue_name)

        self.addCleanup(self.client.delete_queue, queue_name)

        self.assertEqual('201', resp['status'])
        self.assertEqual('', body)


class TestManageQueue(base.BaseQueuingTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(TestManageQueue, cls).setUpClass()
        cls.queues = list()
        for _ in moves.xrange(5):
            queue_name = data_utils.rand_name('Queues-Test')
            cls.queues.append(queue_name)
            # Create Queue
            cls.client.create_queue(queue_name)

    @test.attr(type='smoke')
    def test_delete_queue(self):
        # Delete Queue
        queue_name = self.queues.pop()
        resp, body = self.delete_queue(queue_name)
        self.assertEqual('204', resp['status'])
        self.assertEqual('', body)

    @test.attr(type='smoke')
    def test_check_queue_existence(self):
        # Checking Queue Existence
        for queue_name in self.queues:
            resp, body = self.check_queue_exists(queue_name)
            self.assertEqual('204', resp['status'])
            self.assertEqual('', body)

    @test.attr(type='smoke')
    def test_check_queue_head(self):
        # Checking Queue Existence by calling HEAD
        for queue_name in self.queues:
            resp, body = self.check_queue_exists_head(queue_name)
            self.assertEqual('204', resp['status'])
            self.assertEqual('', body)

    @test.attr(type='smoke')
    def test_list_queues(self):
        # Listing queues
        resp, body = self.list_queues()
        self.assertEqual(len(body['queues']), len(self.queues))
        for item in body['queues']:
            self.assertIn(item['name'], self.queues)

    @test.attr(type='smoke')
    def test_get_queue_stats(self):
        # Retrieve random queue
        queue_name = self.queues[data_utils.rand_int_id(0,
                                                        len(self.queues) - 1)]
        # Get Queue Stats for a newly created Queue
        resp, body = self.get_queue_stats(queue_name)
        msgs = body['messages']
        for element in ('free', 'claimed', 'total'):
            self.assertEqual(0, msgs[element])
        for element in ('oldest', 'newest'):
            self.assertNotIn(element, msgs)

    @test.attr(type='smoke')
    def test_set_and_get_queue_metadata(self):
        # Retrieve random queue
        queue_name = self.queues[data_utils.rand_int_id(0,
                                                        len(self.queues) - 1)]
        # Check the Queue has no metadata
        resp, body = self.get_queue_metadata(queue_name)
        self.assertEqual('200', resp['status'])
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
        resp, body = self.set_queue_metadata(queue_name, req_body)
        self.assertEqual('204', resp['status'])
        self.assertEqual('', body)
        # Get Queue Metadata
        resp, body = self.get_queue_metadata(queue_name)
        self.assertEqual('200', resp['status'])
        self.assertThat(body, matchers.Equals(req_body))

    @classmethod
    def tearDownClass(cls):
        for queue_name in cls.queues:
            cls.client.delete_queue(queue_name)
        super(TestManageQueue, cls).tearDownClass()
