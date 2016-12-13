# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import test


class UsersV3TestJSON(base.BaseIdentityV3AdminTest):

    def _list_users_with_params(self, params, key, expected, not_expected):
        # Helper method to list users filtered with params and
        # assert the response based on expected and not_expected
        # expected: user expected in the list response
        # not_expected: user, which should not be present in list response
        body = self.users_client.list_users(params)['users']
        self.assertIn(expected[key], map(lambda x: x[key], body))
        self.assertNotIn(not_expected[key],
                         map(lambda x: x[key], body))

    @classmethod
    def resource_setup(cls):
        super(UsersV3TestJSON, cls).resource_setup()
        alt_user = data_utils.rand_name('test_user')
        alt_password = data_utils.rand_password()
        cls.alt_email = alt_user + '@testmail.tm'
        # Create a domain
        cls.domain = cls.create_domain()
        # Create user with Domain
        cls.users = list()
        u1_name = data_utils.rand_name('test_user')
        cls.domain_enabled_user = cls.users_client.create_user(
            u1_name, password=alt_password,
            email=cls.alt_email, domain_id=cls.domain['id'])['user']
        cls.users.append(cls.domain_enabled_user)
        # Create default not enabled user
        u2_name = data_utils.rand_name('test_user')
        cls.non_domain_enabled_user = cls.users_client.create_user(
            u2_name, password=alt_password,
            email=cls.alt_email, enabled=False)['user']
        cls.users.append(cls.non_domain_enabled_user)

    @classmethod
    def resource_cleanup(cls):
        # Cleanup the users created during setup
        for user in cls.users:
            cls.users_client.delete_user(user['id'])
        # Cleanup the domain created during setup
        cls.domains_client.update_domain(cls.domain['id'], enabled=False)
        cls.domains_client.delete_domain(cls.domain['id'])
        super(UsersV3TestJSON, cls).resource_cleanup()

    @test.idempotent_id('08f9aabb-dcfe-41d0-8172-82b5fa0bd73d')
    def test_list_user_domains(self):
        # List users with domain
        params = {'domain_id': self.domain['id']}
        self._list_users_with_params(params, 'domain_id',
                                     self.domain_enabled_user,
                                     self.non_domain_enabled_user)

    @test.idempotent_id('bff8bf2f-9408-4ef5-b63a-753c8c2124eb')
    def test_list_users_with_not_enabled(self):
        # List the users with not enabled
        params = {'enabled': False}
        self._list_users_with_params(params, 'enabled',
                                     self.non_domain_enabled_user,
                                     self.domain_enabled_user)

    @test.idempotent_id('c285bb37-7325-4c02-bff3-3da5d946d683')
    def test_list_users_with_name(self):
        # List users with name
        params = {'name': self.domain_enabled_user['name']}
        self._list_users_with_params(params, 'name',
                                     self.domain_enabled_user,
                                     self.non_domain_enabled_user)

    @test.idempotent_id('b30d4651-a2ea-4666-8551-0c0e49692635')
    def test_list_users(self):
        # List users
        body = self.users_client.list_users()['users']
        fetched_ids = [u['id'] for u in body]
        missing_users = [u['id'] for u in self.users
                         if u['id'] not in fetched_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @test.idempotent_id('b4baa3ae-ac00-4b4e-9e27-80deaad7771f')
    def test_get_user(self):
        # Get a user detail
        user = self.users_client.show_user(self.users[0]['id'])['user']
        self.assertEqual(self.users[0]['id'], user['id'])
        self.assertEqual(self.users[0]['name'], user['name'])
        self.assertEqual(self.alt_email, user['email'])
        self.assertEqual(self.domain['id'], user['domain_id'])
