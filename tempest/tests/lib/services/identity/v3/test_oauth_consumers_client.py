# Copyright 2017 AT&T Corporation.
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

from tempest.lib.services.identity.v3 import oauth_consumers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestOAUTHConsumerClient(base.BaseServiceTest):
    FAKE_CREATE_CONSUMER = {
        "consumer": {
            'description': 'A fake description 1'
        }

    }

    FAKE_CONSUMER_INFO = {
        "consumer": {
            'id': '6392c7d3b7a2062e09a07aa377',
            'links': {
                'self': 'http://example.com/identity/v3/' +
                        'OS-OAUTH1/consumers/g6f2l9'
            },
            'description': 'A description that is fake'
        }

    }

    FAKE_LIST_CONSUMERS = {
        'links': {
            'self': 'http://example.com/identity/v3/OS-OAUTH1/consumers/',
            'next': None,
            'previous': None
        },
        'consumers': [
            {
                'id': '6392c7d3b7a2062e09a07aa377',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'OS-OAUTH1/consumers/6b9f2g5'
                },
                'description': 'A description that is fake'
            },
            {
                'id': '677a855c9e3eb3a3954b36aca6',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'OS-OAUTH1/consumers/6a9f2366'
                },
                'description': 'A very fake description 2'
            },
            {
                'id': '9d3ac57b08d65e07826b5e506',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'OS-OAUTH1/consumers/626b5e506'
                },
                'description': 'A very fake description 3'
            },
            {
                'id': 'b522d163b1a18e928aca9y426',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'OS-OAUTH1/consumers/g7ca9426'
                },
                'description': 'A very fake description 4'
            },
            {
                'id': 'b7e47321b5ef9051f93c2049e',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'OS-OAUTH1/consumers/23d82049e'
                },
                'description': 'A very fake description 5'
            }
        ]
    }

    def setUp(self):
        super(TestOAUTHConsumerClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = oauth_consumers_client.OAUTHConsumerClient(fake_auth,
                                                                 'identity',
                                                                 'regionOne')

    def _test_create_consumer(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_consumer,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_CONSUMER,
            bytes_body,
            description=self.FAKE_CREATE_CONSUMER["consumer"]["description"],
            status=201)

    def _test_show_consumer(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_consumer,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CONSUMER_INFO,
            bytes_body,
            consumer_id="6392c7d3b7a2062e09a07aa377")

    def _test_list_consumers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_consumers,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_CONSUMERS,
            bytes_body)

    def _test_update_consumer(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_consumer,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_CONSUMER_INFO,
            bytes_body,
            consumer_id="6392c7d3b7a2062e09a07aa377")

    def test_create_consumer_with_str_body(self):
        self._test_create_consumer()

    def test_create_consumer_with_bytes_body(self):
        self._test_create_consumer(bytes_body=True)

    def test_show_consumer_with_str_body(self):
        self._test_show_consumer()

    def test_show_consumer_with_bytes_body(self):
        self._test_show_consumer(bytes_body=True)

    def test_list_consumers_with_str_body(self):
        self._test_list_consumers()

    def test_list_consumers_with_bytes_body(self):
        self._test_list_consumers(bytes_body=True)

    def test_update_consumer_with_str_body(self):
        self._test_update_consumer()

    def test_update_consumer_with_bytes_body(self):
        self._test_update_consumer(bytes_body=True)

    def test_delete_consumer(self):
        self.check_service_client_function(
            self.client.delete_consumer,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            consumer_id="6392c7d3b7a2062e09a07aa377",
            status=204)
