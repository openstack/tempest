# Copyright 2021 Red Hat, Inc.
# All rights reserved.
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

from tempest.lib.services.network import loggable_resource_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestLoggableResourceClient(base.BaseServiceTest):

    FAKE_LOGS = {
        "loggable_resources": [
            {
                "type": "security_group"
            },
            {
                "type": "none"
            }
        ]
    }

    def setUp(self):
        super(TestLoggableResourceClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.loggable_resource_client = \
            loggable_resource_client.LoggableResourceClient(
                fake_auth, "network", "regionOne")

    def _test_list_loggable_resources(self, bytes_body=False):
        self.check_service_client_function(
            self.loggable_resource_client.list_loggable_resources,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_LOGS,
            bytes_body,
            200)

    def test_list_loggable_resources_with_str_body(self):
        self._test_list_loggable_resources()

    def test_list_loggable_resources_with_bytes_body(self):
        self._test_list_loggable_resources(bytes_body=True)
