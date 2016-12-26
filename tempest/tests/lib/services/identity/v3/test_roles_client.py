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

from tempest.lib.services.identity.v3 import roles_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRolesClient(base.BaseServiceTest):
    FAKE_ROLE_INFO = {
        "role": {
            "domain_id": "1",
            "id": "1",
            "name": "test",
            "links": "example.com"
        }
    }

    FAKE_LIST_ROLES = {
        "roles": [
            {
                "domain_id": "1",
                "id": "1",
                "name": "test",
                "links": "example.com"
            },
            {
                "domain_id": "2",
                "id": "2",
                "name": "test2",
                "links": "example.com"
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
            domain_id="1",
            name="test",
            status=201)

    def _test_show_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_role,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ROLE_INFO,
            bytes_body,
            role_id="1")

    def _test_list_roles(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_roles,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body)

    def _test_update_role(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_role,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_ROLE_INFO,
            bytes_body,
            role_id="1",
            name="test")

    def _test_create_user_role_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_role_on_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_create_user_role_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_list_user_roles_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_roles_on_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def _test_list_user_roles_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_roles_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def _test_create_group_role_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_role_on_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def _test_create_group_role_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def _test_list_group_roles_on_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_roles_on_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123")

    def _test_list_group_roles_on_domain(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_roles_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123")

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

    def test_update_role_with_str_body(self):
        self._test_update_role()

    def test_update_role_with_bytes_body(self):
        self._test_update_role(bytes_body=True)

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

    def test_create_user_role_on_domain_with_str_body(self):
        self._test_create_user_role_on_domain()

    def test_create_user_role_on_domain_with_bytes_body(self):
        self._test_create_user_role_on_domain(bytes_body=True)

    def test_create_group_role_on_domain_with_str_body(self):
        self._test_create_group_role_on_domain()

    def test_create_group_role_on_domain_with_bytes_body(self):
        self._test_create_group_role_on_domain(bytes_body=True)

    def test_list_user_roles_on_project_with_str_body(self):
        self._test_list_user_roles_on_project()

    def test_list_user_roles_on_project_with_bytes_body(self):
        self._test_list_user_roles_on_project(bytes_body=True)

    def test_list_user_roles_on_domain_with_str_body(self):
        self._test_list_user_roles_on_domain()

    def test_list_user_roles_on_domain_with_bytes_body(self):
        self._test_list_user_roles_on_domain(bytes_body=True)

    def test_list_group_roles_on_domain_with_str_body(self):
        self._test_list_group_roles_on_domain()

    def test_list_group_roles_on_domain_with_bytes_body(self):
        self._test_list_group_roles_on_domain(bytes_body=True)

    def test_delete_role_from_user_on_project(self):
        self.check_service_client_function(
            self.client.delete_role_from_user_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_user_on_domain(self):
        self.check_service_client_function(
            self.client.delete_role_from_user_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_group_on_project(self):
        self.check_service_client_function(
            self.client.delete_role_from_group_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_delete_role_from_group_on_domain(self):
        self.check_service_client_function(
            self.client.delete_role_from_group_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_user_role_existence_on_project(self):
        self.check_service_client_function(
            self.client.check_user_role_existence_on_project,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_user_role_existence_on_domain(self):
        self.check_service_client_function(
            self.client.check_user_role_existence_on_domain,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_role_from_group_on_project_existence(self):
        self.check_service_client_function(
            self.client.check_role_from_group_on_project_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_role_from_group_on_domain_existence(self):
        self.check_service_client_function(
            self.client.check_role_from_group_on_domain_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)
