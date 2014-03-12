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
