# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import users_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestUsersClient(base.BaseServiceTest):
    FAKE_CREATE_USER = {
        'user': {
            'default_project_id': '95f8c3f8e7b54409a418fc30717f9ae0',
            'domain_id': '8347b31afc3545c4b311cb4cce788a08',
            'enabled': True,
            'name': 'Tempest User',
            'password': 'TempestPassword',
            "description": "Tempest User",
            "email": "TempestUser@example.com",
            "options": {
                "ignore_password_expiry": True
            }
        }
    }

    FAKE_USER_INFO = {
        'user': {
            'default_project_id': '95f8c3f8e7b54409a418fc30717f9ae0',
            'domain_id': '8347b31afc3545c4b311cb4cce788a08',
            'enabled': True,
            'id': '817fb3c23fd7465ba6d7fe1b1320121d',
            'links': {
                'self': 'http://example.com/identity',
            },
            'name': 'Tempest User',
            'password_expires_at': '2016-11-06T15:32:17.000000',
        }
    }

    FAKE_USER_LIST = {
        'links': {
            'next': None,
            'previous': None,
            'self': 'http://example.com/identity/v3/users',
        },
        'users': [
            {
                'domain_id': 'TempestDomain',
                'enabled': True,
                'id': '817fb3c23fd7465ba6d7fe1b1320121d',
                'links': {
                    'self': 'http://example.com/identity/v3/users/' +
                            '817fb3c23fd7465ba6d7fe1b1320121d',
                },
                'name': 'Tempest User',
                'password_expires_at': '2016-11-06T15:32:17.000000',
            },
            {
                'domain_id': 'TempestDomain',
                'enabled': True,
                'id': 'bdbfb1e2f1344be197e90a778379cca1',
                'links': {
                    'self': 'http://example.com/identity/v3/users/' +
                            'bdbfb1e2f1344be197e90a778379cca1',
                },
                'name': 'Tempest User',
                'password_expires_at': None,
            },
        ]
    }

    FAKE_GROUP_LIST = {
        'links': {
            'self': 'http://example.com/identity/v3/groups',
            'previous': None,
            'next': None,
        },
        'groups': [
            {
                'description': 'Tempest Group One Description',
                'domain_id': 'TempestDomain',
                'id': '1c92f3453ed34291a074b87493455b8f',
                'links': {
                    'self': 'http://example.com/identity/v3/groups/' +
                            '1c92f3453ed34291a074b87493455b8f'
                },
                'name': 'Tempest Group One',
            },
            {
                'description': 'Tempest Group Two Description',
                'domain_id': 'TempestDomain',
                'id': 'ce9e7dafed3b4877a7d4466ed730a9ee',
                'links': {
                    'self': 'http://example.com/identity/v3/groups/' +
                            'ce9e7dafed3b4877a7d4466ed730a9ee'
                },
                'name': 'Tempest Group Two',
            },
        ]
    }

    FAKE_PROJECT_LIST = {
        "links": {
            "self": "http://example.com/identity/v3/users/313233/projects",
            "previous": None,
            "next": None
        },
        "projects": [
            {
                "description": "description of this project",
                "domain_id": "161718",
                "enabled": True,
                "id": "456788",
                "links": {
                    "self": "http://example.com/identity/v3/projects/456788"
                },
                "name": "a project name",
                "parent_id": "212223"
            },
            {
                "description": "description of this project",
                "domain_id": "161718",
                "enabled": True,
                "id": "456789",
                "links": {
                    "self": "http://example.com/identity/v3/projects/456789"
                },
                "name": "another domain",
                "parent_id": "212223"
            },
        ]
    }

    def setUp(self):
        super(TestUsersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = users_client.UsersClient(fake_auth, 'identity',
                                               'regionOne')

    def _test_create_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_USER,
            bytes_body,
            status=201,
        )

    def _test_show_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_user,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
        )

    def _test_list_users(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_users,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_LIST,
            bytes_body,
        )

    def _test_update_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_user,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
            name='NewName',
        )

    def _test_list_user_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_GROUP_LIST,
            bytes_body,
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
        )

    def _test_list_user_projects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_projects,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_PROJECT_LIST,
            bytes_body,
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
        )

    def test_create_user_with_string_body(self):
        self._test_create_user()

    def test_create_user_with_bytes_body(self):
        self._test_create_user(bytes_body=True)

    def test_show_user_with_string_body(self):
        self._test_show_user()

    def test_show_user_with_bytes_body(self):
        self._test_show_user(bytes_body=True)

    def test_list_users_with_string_body(self):
        self._test_list_users()

    def test_list_users_with_bytes_body(self):
        self._test_list_users(bytes_body=True)

    def test_update_user_with_string_body(self):
        self._test_update_user()

    def test_update_user_with_bytes_body(self):
        self._test_update_user(bytes_body=True)

    def test_list_user_groups_with_string_body(self):
        self._test_list_user_groups()

    def test_list_user_groups_with_bytes_body(self):
        self._test_list_user_groups(bytes_body=True)

    def test_list_user_projects_with_string_body(self):
        self._test_list_user_projects()

    def test_list_user_projects_with_bytes_body(self):
        self._test_list_user_projects(bytes_body=True)

    def test_delete_user(self):
        self.check_service_client_function(
            self.client.delete_user,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
            status=204,
        )

    def test_change_user_password(self):
        self.check_service_client_function(
            self.client.update_user_password,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            status=204,
            user_id='817fb3c23fd7465ba6d7fe1b1320121d',
            password='NewTempestPassword',
            original_password='OldTempestPassword')
