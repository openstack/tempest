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

from tempest.lib.services.identity.v2 import roles_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRolesClient(base.BaseServiceTest):
    FAKE_ROLE_INFO = {
        "role": {
            "id": "1",
            "name": "test",
            "description": "test_description"
        }
    }

    FAKE_LIST_ROLES = {
        "roles": [
            {
                "id": "1",
                "name": "test",
                "description": "test_description"
            },
            {
                "id": "2",
                "name": "test2",
                "description": "test2_description"
            }
        ]
    }

    def setUp(self):
        super(TestRolesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = roles_client.RolesClient(fake_auth,
                                               'identity', 'regionOne')

    def _test_create_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_role,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_ROLE_INFO,
            bytes_body,
            id="1",
            name="test",
            description="test_description")

    def _test_show_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_role,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ROLE_INFO,
            bytes_body,
            role_id_or_name="1")

    def _test_list_roles(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_roles,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body)

    def _test_create_user_role_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_role_on_project,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_ROLE_INFO,
            bytes_body,
            tenant_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=200)

    def _test_list_user_roles_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_roles_on_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            tenant_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def test_create_role_with_str_body(self):
        self._test_create_role()

    def test_create_role_with_bytes_body(self):
        self._test_create_role(bytes_body=True)

    def test_show_role_with_str_body(self):
        self._test_show_role()

    def test_show_role_with_bytes_body(self):
        self._test_show_role(bytes_body=True)

    def test_list_roles_with_str_body(self):
        self._test_list_roles()

    def test_list_roles_with_bytes_body(self):
        self._test_list_roles(bytes_body=True)

    def test_delete_role(self):
        self.check_service_client_function(
            self.client.delete_role,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            role_id="1",
            status=204)

    def test_create_user_role_on_project_with_str_body(self):
        self._test_create_user_role_on_project()

    def test_create_user_role_on_project_with_bytes_body(self):
        self._test_create_user_role_on_project(bytes_body=True)

    def test_list_user_roles_on_project_with_str_body(self):
        self._test_list_user_roles_on_project()

    def test_list_user_roles_on_project_with_bytes_body(self):
        self._test_list_user_roles_on_project(bytes_body=True)

    def test_delete_role_from_user_on_project(self):
        self.check_service_client_function(
            self.client.delete_role_from_user_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            tenant_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)
