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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.identity import base
from tempest import test


class TokensV3TestJSON(base.BaseIdentityV3AdminTest):

    @test.attr(type='smoke')
    @test.idempotent_id('0f9f5a5f-d5cd-4a86-8a5b-c5ded151f212')
    def test_tokens(self):
        # Valid user's token is authenticated
        # Create a User
        u_name = data_utils.rand_name('user')
        u_desc = '%s-description' % u_name
        u_email = '%s@testmail.tm' % u_name
        u_password = data_utils.rand_name('pass')
        user = self.client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email)
        self.addCleanup(self.client.delete_user, user['id'])
        # Perform Authentication
        resp = self.token.auth(user_id=user['id'],
                               password=u_password).response
        subject_token = resp['x-subject-token']
        # Perform GET Token
        token_details = self.client.get_token(subject_token)
        self.assertEqual(resp['x-subject-token'], subject_token)
        self.assertEqual(token_details['user']['id'], user['id'])
        self.assertEqual(token_details['user']['name'], u_name)
        # Perform Delete Token
        self.client.delete_token(subject_token)
        self.assertRaises(lib_exc.NotFound, self.client.get_token,
                          subject_token)

    @test.attr(type='gate')
    @test.idempotent_id('565fa210-1da1-4563-999b-f7b5b67cf112')
    def test_rescope_token(self):
        """Rescope a token.

        An unscoped token can be requested, that token can be used to request a
        scoped token. The scoped token can be revoked, and the original token
        used to get a token in a different project.

        """

        # Create a user.
        user_name = data_utils.rand_name(name='user')
        user_password = data_utils.rand_name(name='pass')
        user = self.client.create_user(user_name, password=user_password)
        self.addCleanup(self.client.delete_user, user['id'])

        # Create a couple projects
        project1_name = data_utils.rand_name(name='project')
        project1 = self.client.create_project(project1_name)
        self.addCleanup(self.client.delete_project, project1['id'])

        project2_name = data_utils.rand_name(name='project')
        project2 = self.client.create_project(project2_name)
        self.addCleanup(self.client.delete_project, project2['id'])

        # Create a role
        role_name = data_utils.rand_name(name='role')
        role = self.client.create_role(role_name)
        self.addCleanup(self.client.delete_role, role['id'])

        # Grant the user the role on both projects.
        self.client.assign_user_role(project1['id'], user['id'],
                                     role['id'])

        self.client.assign_user_role(project2['id'], user['id'],
                                     role['id'])

        # Get an unscoped token.
        token_auth = self.token.auth(user_id=user['id'],
                                     password=user_password)

        token_id = token_auth.response['x-subject-token']
        orig_expires_at = token_auth['token']['expires_at']
        orig_issued_at = token_auth['token']['issued_at']
        orig_user = token_auth['token']['user']

        self.assertIsInstance(token_auth['token']['expires_at'], unicode)
        self.assertIsInstance(token_auth['token']['issued_at'], unicode)
        self.assertEqual(['password'], token_auth['token']['methods'])
        self.assertEqual(user['id'], token_auth['token']['user']['id'])
        self.assertEqual(user['name'], token_auth['token']['user']['name'])
        self.assertEqual('default',
                         token_auth['token']['user']['domain']['id'])
        self.assertEqual('Default',
                         token_auth['token']['user']['domain']['name'])
        self.assertNotIn('catalog', token_auth['token'])
        self.assertNotIn('project', token_auth['token'])
        self.assertNotIn('roles', token_auth['token'])

        # Use the unscoped token to get a scoped token.
        token_auth = self.token.auth(token=token_id,
                                     project_name=project1_name,
                                     project_domain_name='Default')
        token1_id = token_auth.response['x-subject-token']

        self.assertEqual(orig_expires_at, token_auth['token']['expires_at'],
                         'Expiration time should match original token')
        self.assertIsInstance(token_auth['token']['issued_at'], unicode)
        self.assertNotEqual(orig_issued_at, token_auth['token']['issued_at'])
        self.assertEqual(set(['password', 'token']),
                         set(token_auth['token']['methods']))
        self.assertEqual(orig_user, token_auth['token']['user'],
                         'User should match original token')
        self.assertIsInstance(token_auth['token']['catalog'], list)
        self.assertEqual(project1['id'],
                         token_auth['token']['project']['id'])
        self.assertEqual(project1['name'],
                         token_auth['token']['project']['name'])
        self.assertEqual('default',
                         token_auth['token']['project']['domain']['id'])
        self.assertEqual('Default',
                         token_auth['token']['project']['domain']['name'])
        self.assertEqual(1, len(token_auth['token']['roles']))
        self.assertEqual(role['id'], token_auth['token']['roles'][0]['id'])
        self.assertEqual(role['name'], token_auth['token']['roles'][0]['name'])

        # Revoke the unscoped token.
        self.client.delete_token(token1_id)

        # Now get another scoped token using the unscoped token.
        token_auth = self.token.auth(token=token_id,
                                     project_name=project2_name,
                                     project_domain_name='Default')

        self.assertEqual(project2['id'],
                         token_auth['token']['project']['id'])
        self.assertEqual(project2['name'],
                         token_auth['token']['project']['name'])
