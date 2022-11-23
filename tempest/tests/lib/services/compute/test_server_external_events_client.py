# Copyright 2022 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.compute import server_external_events_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServerExternalEventsClient(base.BaseServiceTest):

    events = [
        {
            "code": 200,
            "name": "network-changed",
            "server_uuid": "ff1df7b2-6772-45fd-9326-c0a3b05591c2",
            "status": "completed",
            "tag": "foo"
        }
    ]

    events_req = [
        {
            "name": "network-changed",
            "server_uuid": "ff1df7b2-6772-45fd-9326-c0a3b05591c2",
        }
    ]

    def setUp(self):
        super(TestServerExternalEventsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = server_external_events_client.ServerExternalEventsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_server_external_events(self, bytes_body=False):
        expected = {"events": self.events}
        self.check_service_client_function(
            self.client.create_server_external_events,
            'tempest.lib.common.rest_client.RestClient.post', expected,
            bytes_body, events=self.events_req)

    def test_create_server_external_events_str_body(self):
        self._test_create_server_external_events(bytes_body=False)

    def test_create_server_external_events_byte_body(self):
        self._test_create_server_external_events(bytes_body=True)
