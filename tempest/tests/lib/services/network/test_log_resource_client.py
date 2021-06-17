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

import copy

from tempest.lib.services.network import log_resource_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestLogResourceClient(base.BaseServiceTest):

    FAKE_LOGS = {
        "logs": [
            {
                "name": "security group log1",
                "description": "Log for test demo.",
                "id": "2f245a7b-796b-4f26-9cf9-9e82d248fda7",
                "project_id": "92a5a4f4245a4abbafacb7ca73b027b0",
                "tenant_id": "92a5a4f4245a4abbafacb7ca73b027b0",
                "created_at": "2018-04-03T21:03:04Z",
                "updated_at": "2018-04-03T21:03:04Z",
                "enabled": True,
                "revision_number": 1,
                "resource_type": "security_group",
                "resource_id": None,
                "target_id": None,
                "event": "ALL"
            },
            {
                "name": "security group log2",
                "description": "Log for test demo.",
                "id": "46ebaec1-0570-43ac-82f6-60d2b03168c4",
                "project_id": "82a5a4f4245a4abbafacb7ca73b027b0",
                "tenant_id": "82a5a4f4245a4abbafacb7ca73b027b0",
                "created_at": "2018-04-03T21:04:04Z",
                "updated_at": "2018-04-03T21:04:04Z",
                "enabled": True,
                "revision_number": 2,
                "resource_type": "security_group",
                "resource_id": None,
                "target_id": None,
                "event": "ALL"
            }
        ]
    }

    FAKE_LOG_ID = "2f245a7b-796b-4f26-9cf9-9e82d248fda7"

    def setUp(self):
        super(TestLogResourceClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.log_resource_client = log_resource_client.LogResourceClient(
            fake_auth, "network", "regionOne")

    def _test_list_logs(self, bytes_body=False):
        self.check_service_client_function(
            self.log_resource_client.list_logs,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_LOGS,
            bytes_body,
            200)

    def _test_show_log(self, bytes_body=False):
        self.check_service_client_function(
            self.log_resource_client.show_log,
            "tempest.lib.common.rest_client.RestClient.get",
            {"log": self.FAKE_LOGS["logs"][0]},
            bytes_body,
            200,
            log_id=self.FAKE_LOG_ID)

    def _test_create_log(self, bytes_body=False):
        self.check_service_client_function(
            self.log_resource_client.create_log,
            "tempest.lib.common.rest_client.RestClient.post",
            {"logs": self.FAKE_LOGS["logs"][1]},
            bytes_body,
            201,
            log_id="2f245a7b-796b-4f26-9cf9-9e82d248fda7")

    def _test_update_log(self, bytes_body=False):
        update_kwargs = {
            "tenant_id": "83a5a4f4245a4abbafacb7ca73b027b0"
        }

        resp_body = {
            "logs": copy.deepcopy(
                self.FAKE_LOGS["logs"][0]
            )
        }
        resp_body["logs"].update(update_kwargs)

        self.check_service_client_function(
            self.log_resource_client.update_log,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            log_id=self.FAKE_LOG_ID,
            **update_kwargs)

    def test_list_logs_with_str_body(self):
        self._test_list_logs()

    def test_list_logs_with_bytes_body(self):
        self._test_list_logs(bytes_body=True)

    def test_create_log_with_str_body(self):
        self._test_create_log()

    def test_create_log_with_bytes_body(self):
        self._test_create_log(bytes_body=True)

    def test_show_log_with_str_body(self):
        self._test_show_log()

    def test_show_log_with_bytes_body(self):
        self._test_show_log(bytes_body=True)

    def test_update_log_with_str_body(self):
        self._test_update_log()

    def test_update_log_with_bytes_body(self):
        self._test_update_log(bytes_body=True)

    def test_delete_log(self):
        self.check_service_client_function(
            self.log_resource_client.delete_log,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            log_id=self.FAKE_LOG_ID)
