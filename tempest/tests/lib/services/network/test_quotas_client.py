# Copyright 2017 AT&T Corporation.
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

from tempest.lib.services.network import quotas_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestQuotasClient(base.BaseServiceTest):

    FAKE_QUOTAS = {
        "quotas": [
            {
                "floatingip": 50,
                "network": 15,
                "port": 50,
                "project_id": "bab7d5c60cd041a0a36f7c4b6e1dd978",
                "rbac_policy": -1,
                "router": 10,
                "security_group": 10,
                "security_group_rule": 100,
                "subnet": 10,
                "subnetpool": -1,
                "tenant_id": "bab7d5c60cd041a0a36f7c4b6e1dd978"
            }
        ]
    }

    FAKE_PROJECT_QUOTAS = {
        "quota": {
            "floatingip": 50,
            "network": 10,
            "port": 50,
            "rbac_policy": -1,
            "router": 10,
            "security_group": 10,
            "security_group_rule": 100,
            "subnet": 10,
            "subnetpool": -1
        }
    }

    FAKE_QUOTA_TENANT_ID = "bab7d5c60cd041a0a36f7c4b6e1dd978"

    def setUp(self):
        super(TestQuotasClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.quotas_client = quotas_client.QuotasClient(
            fake_auth, "network", "regionOne")

    def _test_list_quotas(self, bytes_body=False):
        self.check_service_client_function(
            self.quotas_client.list_quotas,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_QUOTAS,
            bytes_body,
            200)

    def _test_show_quotas(self, bytes_body=False):
        self.check_service_client_function(
            self.quotas_client.show_quotas,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_PROJECT_QUOTAS,
            bytes_body,
            200,
            tenant_id=self.FAKE_QUOTA_TENANT_ID)

    def _test_show_default_quotas(self, bytes_body=False):
        self.check_service_client_function(
            self.quotas_client.show_default_quotas,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_PROJECT_QUOTAS,
            bytes_body,
            200,
            tenant_id=self.FAKE_QUOTA_TENANT_ID)

    def _test_update_quotas(self, bytes_body=False):
        self.check_service_client_function(
            self.quotas_client.update_quotas,
            "tempest.lib.common.rest_client.RestClient.put",
            self.FAKE_PROJECT_QUOTAS,
            bytes_body,
            200,
            tenant_id=self.FAKE_QUOTA_TENANT_ID)

    def test_reset_quotas(self):
        self.check_service_client_function(
            self.quotas_client.reset_quotas,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            tenant_id=self.FAKE_QUOTA_TENANT_ID)

    def test_list_quotas_with_str_body(self):
        self._test_list_quotas()

    def test_list_quotas_with_bytes_body(self):
        self._test_list_quotas(bytes_body=True)

    def test_show_quotas_with_str_body(self):
        self._test_show_quotas()

    def test_show_quotas_with_bytes_body(self):
        self._test_show_quotas(bytes_body=True)

    def test_show_default_quotas_with_str_body(self):
        self._test_show_default_quotas()

    def test_show_default_quotas_with_bytes_body(self):
        self._test_show_default_quotas(bytes_body=True)

    def test_update_quotas_with_str_body(self):
        self._test_update_quotas()

    def test_update_quotas_with_bytes_body(self):
        self._test_update_quotas(bytes_body=True)
