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

from tempest.lib.services.identity.v3 import inherited_roles_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestInheritedRolesClient(base.BaseServiceTest):
    FAKE_LIST_INHERITED_ROLES = {
        "roles": [
            {
                "id": "1",
                "name": "test",
                "links": "example.com"
            },
            {
                "id": "2",
                "name": "test2",
                "links": "example.com"
            }
        ]
    }

    def setUp(self):
        super(TestInheritedRolesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = inherited_roles_client.InheritedRolesClient(
            fake_auth, 'identity', 'regionOne')

    def _test_create_inherited_role_on_domains_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_inherited_role_on_domains_user,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_list_inherited_project_role_for_user_on_domain(
        self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_inherited_project_role_for_user_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_INHERITED_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123")

    def _test_create_inherited_role_on_domains_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_inherited_role_on_domains_group,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def _test_list_inherited_project_role_for_group_on_domain(
        self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_inherited_project_role_for_group_on_domain,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_INHERITED_ROLES,
            bytes_body,
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123")

    def _test_create_inherited_role_on_projects_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_inherited_role_on_projects_user,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def _test_create_inherited_role_on_projects_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_inherited_role_on_projects_group,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_create_inherited_role_on_domains_user_with_str_body(self):
        self._test_create_inherited_role_on_domains_user()

    def test_create_inherited_role_on_domains_user_with_bytes_body(self):
        self._test_create_inherited_role_on_domains_user(bytes_body=True)

    def test_create_inherited_role_on_domains_group_with_str_body(self):
        self._test_create_inherited_role_on_domains_group()

    def test_create_inherited_role_on_domains_group_with_bytes_body(self):
        self._test_create_inherited_role_on_domains_group(bytes_body=True)

    def test_create_inherited_role_on_projects_user_with_str_body(self):
        self._test_create_inherited_role_on_projects_user()

    def test_create_inherited_role_on_projects_group_with_bytes_body(self):
        self._test_create_inherited_role_on_projects_group(bytes_body=True)

    def test_list_inherited_project_role_for_user_on_domain_with_str_body(
        self):
        self._test_list_inherited_project_role_for_user_on_domain()

    def test_list_inherited_project_role_for_user_on_domain_with_bytes_body(
        self):
        self._test_list_inherited_project_role_for_user_on_domain(
            bytes_body=True)

    def test_list_inherited_project_role_for_group_on_domain_with_str_body(
        self):
        self._test_list_inherited_project_role_for_group_on_domain()

    def test_list_inherited_project_role_for_group_on_domain_with_bytes_body(
        self):
        self._test_list_inherited_project_role_for_group_on_domain(
            bytes_body=True)

    def test_delete_inherited_role_from_user_on_domain(self):
        self.check_service_client_function(
            self.client.delete_inherited_role_from_user_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_user_inherited_project_role_on_domain(self):
        self.check_service_client_function(
            self.client.check_user_inherited_project_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_inherited_role_from_group_on_domain(self):
        self.check_service_client_function(
            self.client.delete_inherited_role_from_group_on_domain,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_group_inherited_project_role_on_domain(self):
        self.check_service_client_function(
            self.client.check_group_inherited_project_role_on_domain,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            domain_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_delete_inherited_role_from_user_on_project(self):
        self.check_service_client_function(
            self.client.delete_inherited_role_from_user_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_check_user_has_flag_on_inherited_to_project(self):
        self.check_service_client_function(
            self.client.check_user_has_flag_on_inherited_to_project,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            user_id="123",
            role_id="1234",
            status=204)

    def test_delete_inherited_role_from_group_on_project(self):
        self.check_service_client_function(
            self.client.delete_inherited_role_from_group_on_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)

    def test_check_group_has_flag_on_inherited_to_project(self):
        self.check_service_client_function(
            self.client.check_group_has_flag_on_inherited_to_project,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            project_id="b344506af7644f6794d9cb316600b020",
            group_id="123",
            role_id="1234",
            status=204)
