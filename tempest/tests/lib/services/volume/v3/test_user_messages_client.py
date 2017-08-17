# Copyright 2016 Red Hat.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.volume.v3 import messages_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestUserMessagesClient(base.BaseServiceTest):
    USER_MESSAGE_INFO = {
        "created_at": "2016-11-21T06:16:34.000000",
        "guaranteed_until": "2016-12-21T06:16:34.000000",
        "user_message": "No storage could be allocated for this volume "
                        "request. You may be able to try another size or"
                        " volume type.",
        "resource_uuid": "c570b406-bf0b-4067-9398-f0bb09a7d9d7",
        "request_id": "req-8f68681e-9b6b-4009-b94c-ac0811595451",
        "message_level": "ERROR",
        "id": "9a7dafbd-a156-4540-8996-50e71b5dcadf",
        "resource_type": "VOLUME",
        "links": [
            {"href": "http://192.168.100.230:8776/v3/"
                     "a678cb65f701462ea2257245cd640829/messages/"
                     "9a7dafbd-a156-4540-8996-50e71b5dcadf",
             "rel": "self"},
            {"href": "http://192.168.100.230:8776/"
                     "a678cb65f701462ea2257245cd640829/messages/"
                     "9a7dafbd-a156-4540-8996-50e71b5dcadf",
             "rel": "bookmark"}]
        }
    FAKE_SHOW_USER_MESSAGE = {
        "message": dict(event_id="000002", **USER_MESSAGE_INFO)}

    FAKE_LIST_USER_MESSAGES = {
        "messages": [
            dict(event_id="000003", **USER_MESSAGE_INFO),
            dict(event_id="000004", **USER_MESSAGE_INFO)
        ]
    }

    def setUp(self):
        super(TestUserMessagesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = messages_client.MessagesClient(fake_auth,
                                                     'volume',
                                                     'regionOne')

    def _test_show_user_message(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_message,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_USER_MESSAGE,
            bytes_body,
            message_id="9a7dafbd-a156-4540-8996-50e71b5dcadf")

    def _test_list_user_message(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_messages,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_USER_MESSAGES,
            bytes_body)

    def test_list_user_message_with_str_body(self):
        self._test_list_user_message()

    def test_list_user_message_with_bytes_body(self):
        self._test_list_user_message(bytes_body=True)

    def test_show_user_message_with_str_body(self):
        self._test_show_user_message()

    def test_show_user_message_with_bytes_body(self):
        self._test_show_user_message(bytes_body=True)

    def test_delete_user_message(self):
        self.check_service_client_function(
            self.client.delete_message,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            message_id="9a7dafbd-a156-4540-8996-50e71b5dcadf",
            status=204)
