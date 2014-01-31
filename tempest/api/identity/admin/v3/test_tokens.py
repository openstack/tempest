# Copyright 2012 OpenStack Foundation
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
from tempest import exceptions
from tempest.test import attr


class UsersTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @attr(type='smoke')
    def test_tokens(self):
        # Valid user's token is authenticated
        # Create a User
        u_name = data_utils.rand_name('user-')
        u_desc = '%s-description' % u_name
        u_email = '%s@testmail.tm' % u_name
        u_password = data_utils.rand_name('pass-')
        resp, user = self.client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email)
        self.assertTrue(resp['status'].startswith('2'))
        self.addCleanup(self.client.delete_user, user['id'])
        # Perform Authentication
        resp, body = self.token.auth(user['id'], u_password)
        self.assertEqual(resp['status'], '201')
        subject_token = resp['x-subject-token']
        # Perform GET Token
        resp, token_details = self.client.get_token(subject_token)
        self.assertEqual(resp['status'], '200')
        self.assertEqual(resp['x-subject-token'], subject_token)
        self.assertEqual(token_details['user']['id'], user['id'])
        self.assertEqual(token_details['user']['name'], u_name)
        # Perform Delete Token
        resp, _ = self.client.delete_token(subject_token)
        self.assertRaises(exceptions.NotFound, self.client.get_token,
                          subject_token)


class UsersTestXML(UsersTestJSON):
    _interface = 'xml'
