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

from tempest_lib.common.utils import data_utils

from tempest.api.messaging import base
from tempest import config
from tempest import test


LOG = logging.getLogger(__name__)
CONF = config.CONF


class TestMessages(base.BaseMessagingTest):

    @classmethod
    def resource_setup(cls):
        super(TestMessages, cls).resource_setup()
        cls.queue_name = data_utils.rand_name('Queues-Test')
        # Create Queue
        cls.client.create_queue(cls.queue_name)

    def _post_messages(self, repeat=CONF.messaging.max_messages_per_page):
        message_body = self.generate_message_body(repeat=repeat)
        resp, body = self.post_messages(queue_name=self.queue_name,
                                        rbody=message_body)
        return resp, body

    @test.attr(type='smoke')
    @test.idempotent_id('93867172-a414-4eb3-a639-96e943c516b4')
    def test_post_messages(self):
        # Post Messages
        resp, _ = self._post_messages()

        # Get on the posted messages
        message_uri = resp['location']
        resp, _ = self.client.get_multiple_messages(message_uri)
        # The test has an assertion here, because the response cannot be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('200', resp['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('c967d59a-e919-41cb-994b-1c4300452c80')
    def test_list_messages(self):
        # Post Messages
        self._post_messages()

        # List Messages
        resp, _ = self.list_messages(queue_name=self.queue_name)
        # The test has an assertion here, because the response cannot be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('200', resp['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('2a68e3de-24df-47c3-9039-ec4156656bf8')
    def test_get_message(self):
        # Post Messages
        _, body = self._post_messages()
        message_uri = body['resources'][0]

        # Get posted message
        resp, _ = self.client.get_single_message(message_uri)
        # The test has an assertion here, because the response cannot be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('200', resp['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('c4b0a30b-efda-4b87-a395-0c43140df74d')
    def test_get_multiple_messages(self):
        # Post Messages
        resp, _ = self._post_messages()
        message_uri = resp['location']

        # Get posted messages
        resp, _ = self.client.get_multiple_messages(message_uri)
        # The test has an assertion here, because the response cannot be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('200', resp['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('fc0fca47-dd8b-4ecc-8522-d9c191f9bc9f')
    def test_delete_single_message(self):
        # Post Messages
        _, body = self._post_messages()
        message_uri = body['resources'][0]

        # Delete posted message & verify the delete operration
        self.client.delete_messages(message_uri)

        message_uri = message_uri.replace('/messages/', '/messages?ids=')
        resp, _ = self.client.get_multiple_messages(message_uri)
        # The test has an assertion here, because the response has to be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('00cca069-5c8f-4b42-bff1-c577da2a4546')
    def test_delete_multiple_messages(self):
        # Post Messages
        resp, _ = self._post_messages()
        message_uri = resp['location']

        # Delete multiple messages
        self.client.delete_messages(message_uri)
        resp, _ = self.client.get_multiple_messages(message_uri)
        # The test has an assertion here, because the response has to be 204
        # in this case (the client allows 200 or 204 for this API call).
        self.assertEqual('204', resp['status'])

    @classmethod
    def resource_cleanup(cls):
        cls.delete_queue(cls.queue_name)
        super(TestMessages, cls).resource_cleanup()
