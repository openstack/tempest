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

from tempest.lib.services.identity.v3 import groups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestGroupsClient(base.BaseServiceTest):
    FAKE_CREATE_GROUP = {
        'group': {
            'description': 'Tempest Group Description',
            'domain_id': 'TempestDomain',
            'name': 'Tempest Group',
        }
    }

    FAKE_GROUP_INFO = {
        'group': {
            'description': 'Tempest Group Description',
            'domain_id': 'TempestDomain',
            'id': '6e13e2068cf9466e98950595baf6bb35',
            'links': {
                'self': 'http://example.com/identity/v3/groups/' +
                        '6e13e2068cf9466e98950595baf6bb35'
            },
            'name': 'Tempest Group',
        }
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

    FAKE_USER_LIST = {
        'links': {
            'self': 'http://example.com/identity/v3/groups/' +
                    '6e13e2068cf9466e98950595baf6bb35/users',
            'previous': None,
            'next': None,
        },
        'users': [
            {
                'domain_id': 'TempestDomain',
                'description': 'Tempest Test User One Description',
                'enabled': True,
                'id': '642688fa65a84217b86cef3c063de2b9',
                'name': 'TempestUserOne',
                'links': {
                    'self': 'http://example.com/identity/v3/users/' +
                            '642688fa65a84217b86cef3c063de2b9'
                }
            },
            {
                'domain_id': 'TempestDomain',
                'description': 'Tempest Test User Two Description',
                'enabled': True,
                'id': '1048ead6f8ef4a859b44ffbce3ac0b52',
                'name': 'TempestUserTwo',
                'links': {
                    'self': 'http://example.com/identity/v3/users/' +
                            '1048ead6f8ef4a859b44ffbce3ac0b52'
                }
            },
        ]
    }

    def setUp(self):
        super(TestGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = groups_client.GroupsClient(fake_auth, 'identity',
                                                 'regionOne')

    def _test_create_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP,
            bytes_body,
            status=201,
        )

    def _test_show_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_GROUP_INFO,
            bytes_body,
            group_id='6e13e2068cf9466e98950595baf6bb35',
        )

    def _test_list_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_GROUP_LIST,
            bytes_body,
        )

    def _test_update_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_group,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_GROUP_INFO,
            bytes_body,
            group_id='6e13e2068cf9466e98950595baf6bb35',
            name='NewName',
        )

    def _test_list_users_in_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_users,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_LIST,
            bytes_body,
            group_id='6e13e2068cf9466e98950595baf6bb35',
        )

    def test_create_group_with_string_body(self):
        self._test_create_group()

    def test_create_group_with_bytes_body(self):
        self._test_create_group(bytes_body=True)

    def test_show_group_with_string_body(self):
        self._test_show_group()

    def test_show_group_with_bytes_body(self):
        self._test_show_group(bytes_body=True)

    def test_list_groups_with_string_body(self):
        self._test_list_groups()

    def test_list_groups_with_bytes_body(self):
        self._test_list_groups(bytes_body=True)

    def test_update_group_with_string_body(self):
        self._test_update_group()

    def test_update_group_with_bytes_body(self):
        self._test_update_group(bytes_body=True)

    def test_list_users_in_group_with_string_body(self):
        self._test_list_users_in_group()

    def test_list_users_in_group_with_bytes_body(self):
        self._test_list_users_in_group(bytes_body=True)

    def test_delete_group(self):
        self.check_service_client_function(
            self.client.delete_group,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            group_id='6e13e2068cf9466e98950595baf6bb35',
            status=204,
        )

    def test_add_user_to_group(self):
        self.check_service_client_function(
            self.client.add_group_user,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            status=204,
            group_id='6e13e2068cf9466e98950595baf6bb35',
            user_id='642688fa65a84217b86cef3c063de2b9',
        )

    def test_check_user_in_group(self):
        self.check_service_client_function(
            self.client.check_group_user_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            status=204,
            group_id='6e13e2068cf9466e98950595baf6bb35',
            user_id='642688fa65a84217b86cef3c063de2b9',
        )
