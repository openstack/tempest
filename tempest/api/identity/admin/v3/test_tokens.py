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
from tempest import test


class TokensV3TestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @test.attr(type='smoke')
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
        self.assertEqual(201, resp.status)
        self.addCleanup(self.client.delete_user, user['id'])
        # Perform Authentication
        resp, body = self.token.auth(user['id'], u_password)
        self.assertEqual(201, resp.status)
        subject_token = resp['x-subject-token']
        # Perform GET Token
        resp, token_details = self.client.get_token(subject_token)
        self.assertEqual(200, resp.status)
        self.assertEqual(resp['x-subject-token'], subject_token)
        self.assertEqual(token_details['user']['id'], user['id'])
        self.assertEqual(token_details['user']['name'], u_name)
        # Perform Delete Token
        resp, _ = self.client.delete_token(subject_token)
        self.assertRaises(exceptions.NotFound, self.client.get_token,
                          subject_token)

    @test.attr(type='gate')
    def test_rescope_token(self):
        """Rescope a token.

        An unscoped token can be requested, that token can be used to request a
        scoped token. The scoped token can be revoked, and the original token
        used to get a token in a different project.

        """

        # Create a user.
        user_name = data_utils.rand_name(name='user-')
        user_password = data_utils.rand_name(name='pass-')
        resp, user = self.client.create_user(user_name, password=user_password)
        self.assertEqual(201, resp.status)
        self.addCleanup(self.client.delete_user, user['id'])

        # Create a couple projects
        project1_name = data_utils.rand_name(name='project-')
        resp, project1 = self.client.create_project(project1_name)
        self.assertEqual(201, resp.status)
        self.addCleanup(self.client.delete_project, project1['id'])

        project2_name = data_utils.rand_name(name='project-')
        resp, project2 = self.client.create_project(project2_name)
        self.assertEqual(201, resp.status)
        self.addCleanup(self.client.delete_project, project2['id'])

        # Create a role
        role_name = data_utils.rand_name(name='role-')
        resp, role = self.client.create_role(role_name)
        self.assertEqual(201, resp.status)
        self.addCleanup(self.client.delete_role, role['id'])

        # Grant the user the role on both projects.
        resp, _ = self.client.assign_user_role(project1['id'], user['id'],
                                               role['id'])
        self.assertEqual(204, resp.status)

        resp, _ = self.client.assign_user_role(project2['id'], user['id'],
                                               role['id'])
        self.assertEqual(204, resp.status)

        # Get an unscoped token.
        resp, token_auth = self.token.auth(user=user['id'],
                                           password=user_password)
        self.assertEqual(201, resp.status)

        token_id = resp['x-subject-token']
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
        resp, token_auth = self.token.auth(token=token_id,
                                           tenant=project1_name,
                                           domain='Default')
        token1_id = resp['x-subject-token']
        self.assertEqual(201, resp.status)

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
        resp, _ = self.client.delete_token(token1_id)
        self.assertEqual(204, resp.status)

        # Now get another scoped token using the unscoped token.
        resp, token_auth = self.token.auth(token=token_id,
                                           tenant=project2_name,
                                           domain='Default')
        self.assertEqual(201, resp.status)

        self.assertEqual(project2['id'],
                         token_auth['token']['project']['id'])
        self.assertEqual(project2['name'],
                         token_auth['token']['project']['name'])


class TokensV3TestXML(TokensV3TestJSON):
    _interface = 'xml'
