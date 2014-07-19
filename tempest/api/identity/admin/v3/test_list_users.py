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
    _interface = 'json'

    def _list_users_with_params(self, params, key, expected, not_expected):
        # Helper method to list users filtered with params and
        # assert the response based on expected and not_expected
        # expected: user expected in the list response
        # not_expected: user, which should not be present in list response
        _, body = self.client.get_users(params)
        self.assertIn(expected[key], map(lambda x: x[key], body))
        self.assertNotIn(not_expected[key],
                         map(lambda x: x[key], body))

    @classmethod
    def setUpClass(cls):
        super(UsersV3TestJSON, cls).setUpClass()
        alt_user = data_utils.rand_name('test_user')
        alt_password = data_utils.rand_name('pass')
        cls.alt_email = alt_user + '@testmail.tm'
        cls.data.setup_test_domain()
        # Create user with Domain
        u1_name = data_utils.rand_name('test_user')
        _, cls.domain_enabled_user = cls.client.create_user(
            u1_name, password=alt_password,
            email=cls.alt_email, domain_id=cls.data.domain['id'])
        cls.data.v3_users.append(cls.domain_enabled_user)
        # Create default not enabled user
        u2_name = data_utils.rand_name('test_user')
        _, cls.non_domain_enabled_user = cls.client.create_user(
            u2_name, password=alt_password,
            email=cls.alt_email, enabled=False)
        cls.data.v3_users.append(cls.non_domain_enabled_user)

    @test.attr(type='gate')
    def test_list_user_domains(self):
        # List users with domain
        params = {'domain_id': self.data.domain['id']}
        self._list_users_with_params(params, 'domain_id',
                                     self.domain_enabled_user,
                                     self.non_domain_enabled_user)

    @test.attr(type='gate')
    def test_list_users_with_not_enabled(self):
        # List the users with not enabled
        params = {'enabled': False}
        self._list_users_with_params(params, 'enabled',
                                     self.non_domain_enabled_user,
                                     self.domain_enabled_user)

    @test.attr(type='gate')
    def test_list_users_with_name(self):
        # List users with name
        params = {'name': self.domain_enabled_user['name']}
        self._list_users_with_params(params, 'name',
                                     self.domain_enabled_user,
                                     self.non_domain_enabled_user)

    @test.attr(type='gate')
    def test_list_users(self):
        # List users
        _, body = self.client.get_users()
        fetched_ids = [u['id'] for u in body]
        missing_users = [u['id'] for u in self.data.v3_users
                         if u['id'] not in fetched_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @test.attr(type='gate')
    def test_get_user(self):
        # Get a user detail
        _, user = self.client.get_user(self.data.v3_users[0]['id'])
        self.assertEqual(self.data.v3_users[0]['id'], user['id'])
        self.assertEqual(self.data.v3_users[0]['name'], user['name'])
        self.assertEqual(self.alt_email, user['email'])
        self.assertEqual(self.data.domain['id'], user['domain_id'])


class UsersV3TestXML(UsersV3TestJSON):
    _interface = 'xml'
