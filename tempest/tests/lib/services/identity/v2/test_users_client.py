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

from tempest.lib.services.identity.v2 import users_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestUsersClient(base.BaseServiceTest):
    FAKE_USER_INFO = {
        "user": {
            "id": "1",
            "name": "test",
            "email": "john.smith@example.org",
            "enabled": True
        }
    }

    FAKE_LIST_USERS = {
        "users": [
            {
                "id": "1",
                "name": "test",
                "email": "john.smith@example.org",
                "enabled": True
            },
            {
                "id": "2",
                "name": "test2",
                "email": "john.smith@example.org",
                "enabled": True
            }
        ]
    }

    FAKE_USER_EC2_CREDENTIAL_INFO = {
        "credential": {
            'user_id': '9beb0e12f3e5416db8d7cccfc785db3b',
            'access': '79abf59acc77492a86170cbe2f1feafa',
            'secret': 'c4e7d3a691fd4563873d381a40320f46',
            'trust_id': None,
            'tenant_id': '596557269d7b4dd78631a602eb9f151d'
        }
    }

    FAKE_LIST_USER_EC2_CREDENTIALS = {
        "credentials": [
            {
                'user_id': '9beb0e12f3e5416db8d7cccfc785db3b',
                'access': '79abf59acc77492a86170cbe2f1feafa',
                'secret': 'c4e7d3a691fd4563873d381a40320f46',
                'trust_id': None,
                'tenant_id': '596557269d7b4dd78631a602eb9f151d'
            },
            {
                'user_id': '3beb0e12f3e5416db8d7cccfc785de4r',
                'access': '45abf59acc77492a86170cbe2f1fesde',
                'secret': 'g4e7d3a691fd4563873d381a40320e45',
                'trust_id': None,
                'tenant_id': '123557269d7b4dd78631a602eb9f112f'
            }
        ]
    }

    def setUp(self):
        super(TestUsersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = users_client.UsersClient(fake_auth,
                                               'identity', 'regionOne')

    def _test_create_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_USER_INFO,
            bytes_body,
            name="test",
            email="john.smith@example.org")

    def _test_update_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_user,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id="1",
            name="test")

    def _test_show_user(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_user,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id="1")

    def _test_list_users(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_users,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_USERS,
            bytes_body)

    def _test_update_user_enabled(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_user_enabled,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id="1",
            enabled=True)

    def _test_update_user_password(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_user_password,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id="1",
            password="pass")

    def _test_update_user_own_password(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_user_own_password,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_USER_INFO,
            bytes_body,
            user_id="1",
            password="pass")

    def _test_create_user_ec2_credential(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_user_ec2_credential,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_USER_EC2_CREDENTIAL_INFO,
            bytes_body,
            user_id="1",
            tenant_id="123")

    def _test_show_user_ec2_credential(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_user_ec2_credential,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_USER_EC2_CREDENTIAL_INFO,
            bytes_body,
            user_id="1",
            access="123")

    def _test_list_user_ec2_credentials(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_user_ec2_credentials,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_USER_EC2_CREDENTIALS,
            bytes_body,
            user_id="1")

    def test_create_user_with_str_body(self):
        self._test_create_user()

    def test_create_user_with_bytes_body(self):
        self._test_create_user(bytes_body=True)

    def test_update_user_with_str_body(self):
        self._test_update_user()

    def test_update_user_with_bytes_body(self):
        self._test_update_user(bytes_body=True)

    def test_show_user_with_str_body(self):
        self._test_show_user()

    def test_show_user_with_bytes_body(self):
        self._test_show_user(bytes_body=True)

    def test_list_users_with_str_body(self):
        self._test_list_users()

    def test_list_users_with_bytes_body(self):
        self._test_list_users(bytes_body=True)

    def test_delete_user(self):
        self.check_service_client_function(
            self.client.delete_user,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id="1",
            status=204)

    def test_update_user_enabled_with_str_body(self):
        self._test_update_user_enabled()

    def test_update_user_enabled_with_bytes_body(self):
        self._test_update_user_enabled(bytes_body=True)

    def test_update_user_password_with_str_body(self):
        self._test_update_user_password()

    def test_update_user_password_with_bytes_body(self):
        self._test_update_user_password(bytes_body=True)

    def test_update_user_own_password_with_str_body(self):
        self._test_update_user_own_password()

    def test_update_user_own_password_with_bytes_body(self):
        self._test_update_user_own_password(bytes_body=True)

    def test_create_user_ec2_credential_with_str_body(self):
        self._test_create_user_ec2_credential()

    def test_create_user_ec2_credential_with_bytes_body(self):
        self._test_create_user_ec2_credential(bytes_body=True)

    def test_show_user_ec2_credential_with_str_body(self):
        self._test_show_user_ec2_credential()

    def test_show_user_ec2_credential_with_bytes_body(self):
        self._test_show_user_ec2_credential(bytes_body=True)

    def test_list_user_ec2_credentials_with_str_body(self):
        self._test_list_user_ec2_credentials()

    def test_list_user_ec2_credentials_with_bytes_body(self):
        self._test_list_user_ec2_credentials(bytes_body=True)

    def test_delete_user_ec2_credential(self):
        self.check_service_client_function(
            self.client.delete_user_ec2_credential,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id="123",
            access="1234",
            status=204)
