# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.identity.v2 import tenants_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTenantsClient(base.BaseServiceTest):
    FAKE_TENANT_INFO = {
        "tenant": {
            "id": "1",
            "name": "test",
            "description": "test_description",
            "enabled": True
        }
    }

    FAKE_LIST_TENANTS = {
        "tenants": [
            {
                "id": "1",
                "name": "test",
                "description": "test_description",
                "enabled": True
            },
            {
                "id": "2",
                "name": "test2",
                "description": "test2_description",
                "enabled": True
            }
        ]
    }

    def setUp(self):
        super(TestTenantsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = tenants_client.TenantsClient(fake_auth,
                                                   'identity', 'regionOne')

    def _test_create_tenant(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_tenant,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_TENANT_INFO,
            bytes_body,
            name="test",
            description="test_description")

    def _test_show_tenant(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_tenant,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_TENANT_INFO,
            bytes_body,
            tenant_id="1")

    def _test_update_tenant(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_tenant,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_TENANT_INFO,
            bytes_body,
            tenant_id="1",
            name="test",
            description="test_description")

    def _test_list_tenants(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_tenants,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_TENANTS,
            bytes_body)

    def _test_list_tenant_users(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_tenant_users,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_TENANTS,
            bytes_body,
            tenant_id="1")

    def test_create_tenant_with_str_body(self):
        self._test_create_tenant()

    def test_create_tenant_with_bytes_body(self):
        self._test_create_tenant(bytes_body=True)

    def test_show_tenant_with_str_body(self):
        self._test_show_tenant()

    def test_show_tenant_with_bytes_body(self):
        self._test_show_tenant(bytes_body=True)

    def test_update_tenant_with_str_body(self):
        self._test_update_tenant()

    def test_update_tenant_with_bytes_body(self):
        self._test_update_tenant(bytes_body=True)

    def test_list_tenants_with_str_body(self):
        self._test_list_tenants()

    def test_list_tenants_with_bytes_body(self):
        self._test_list_tenants(bytes_body=True)

    def test_delete_tenant(self):
        self.check_service_client_function(
            self.client.delete_tenant,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            tenant_id="1",
            status=204)

    def test_list_tenant_users_with_str_body(self):
        self._test_list_tenant_users()

    def test_list_tenant_users_with_bytes_body(self):
        self._test_list_tenant_users(bytes_body=True)
