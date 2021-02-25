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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class TokensV3TestJSON(base.BaseIdentityV3AdminTest):
    """Test tokens"""

    credentials = ['primary', 'admin', 'alt']

    @decorators.idempotent_id('565fa210-1da1-4563-999b-f7b5b67cf112')
    def test_rescope_token(self):
        """Rescope a token.

        An unscoped token can be requested, that token can be used to request a
        scoped token. The scoped token can be revoked, and the original token
        used to get a token in a different project.

        """

        # Create a user.
        user_password = data_utils.rand_password()
        user = self.create_test_user(password=user_password)

        # Create a couple projects
        project1_name = data_utils.rand_name(name=self.__class__.__name__)
        project1 = self.setup_test_project(name=project1_name)

        project2_name = data_utils.rand_name(name=self.__class__.__name__)
        project2 = self.setup_test_project(name=project2_name)
        self.addCleanup(self.projects_client.delete_project, project2['id'])

        # Create a role
        role = self.setup_test_role()

        # Grant the user the role on both projects.
        self.roles_client.create_user_role_on_project(project1['id'],
                                                      user['id'],
                                                      role['id'])

        self.roles_client.create_user_role_on_project(project2['id'],
                                                      user['id'],
                                                      role['id'])

        # Get an unscoped token.
        token_auth = self.token.auth(user_id=user['id'],
                                     password=user_password)

        token_id = token_auth.response['x-subject-token']
        orig_expires_at = token_auth['token']['expires_at']
        orig_user = token_auth['token']['user']

        self.assertIsInstance(token_auth['token']['expires_at'], str)
        self.assertIsInstance(token_auth['token']['issued_at'], str)
        self.assertEqual(['password'], token_auth['token']['methods'])
        self.assertEqual(user['id'], token_auth['token']['user']['id'])
        self.assertEqual(user['name'], token_auth['token']['user']['name'])
        self.assertEqual(CONF.identity.default_domain_id,
                         token_auth['token']['user']['domain']['id'])
        self.assertIsNotNone(token_auth['token']['user']['domain']['name'])
        self.assertNotIn('catalog', token_auth['token'])
        self.assertNotIn('project', token_auth['token'])
        self.assertNotIn('roles', token_auth['token'])

        # Use the unscoped token to get a scoped token.
        token_auth = self.token.auth(
            token=token_id,
            project_name=project1_name,
            project_domain_id=CONF.identity.default_domain_id)
        token1_id = token_auth.response['x-subject-token']

        self.assertEqual(orig_expires_at, token_auth['token']['expires_at'],
                         'Expiration time should match original token')
        self.assertIsInstance(token_auth['token']['issued_at'], str)
        self.assertEqual(set(['password', 'token']),
                         set(token_auth['token']['methods']))
        self.assertEqual(orig_user, token_auth['token']['user'],
                         'User should match original token')
        self.assertIsInstance(token_auth['token']['catalog'], list)
        self.assertEqual(project1['id'],
                         token_auth['token']['project']['id'])
        self.assertEqual(project1['name'],
                         token_auth['token']['project']['name'])
        self.assertEqual(CONF.identity.default_domain_id,
                         token_auth['token']['project']['domain']['id'])
        self.assertIsNotNone(token_auth['token']['project']['domain']['name'])
        self.assertEqual(1, len(token_auth['token']['roles']))
        self.assertEqual(role['id'], token_auth['token']['roles'][0]['id'])
        self.assertEqual(role['name'], token_auth['token']['roles'][0]['name'])

        # Revoke the unscoped token.
        self.client.delete_token(token1_id)

        # Now get another scoped token using the unscoped token.
        token_auth = self.token.auth(
            token=token_id,
            project_name=project2_name,
            project_domain_id=CONF.identity.default_domain_id)

        self.assertEqual(project2['id'],
                         token_auth['token']['project']['id'])
        self.assertEqual(project2['name'],
                         token_auth['token']['project']['name'])

    @decorators.idempotent_id('08ed85ce-2ba8-4864-b442-bcc61f16ae89')
    def test_get_available_project_scopes(self):
        """Test getting available project scopes"""
        manager_project_id = self.os_primary.credentials.project_id
        admin_user_id = self.os_admin.credentials.user_id
        admin_role_id = self.get_role_by_name(CONF.identity.admin_role)['id']

        # Grant the user the role on both projects.
        self.roles_client.create_user_role_on_project(
            manager_project_id, admin_user_id, admin_role_id)
        self.addCleanup(
            self.roles_client.delete_role_from_user_on_project,
            manager_project_id, admin_user_id, admin_role_id)

        assigned_project_ids = [self.os_admin.credentials.project_id,
                                manager_project_id]

        # Get available project scopes
        available_projects = self.client.list_auth_projects()['projects']

        # Create list to save fetched project IDs
        fetched_project_ids = [i['id'] for i in available_projects]

        # verifying the project ids in list
        missing_project_ids = \
            [p for p in assigned_project_ids if p not in fetched_project_ids]
        self.assertEmpty(missing_project_ids,
                         "Failed to find project_ids %s in fetched list" %
                         ', '.join(missing_project_ids))

    @decorators.idempotent_id('ec5ecb05-af64-4c04-ac86-4d9f6f12f185')
    def test_get_available_domain_scopes(self):
        """Test getting available domain scopes

        To verify that listing domain scopes for a user works if
        the user has a domain role or belongs to a group that has a domain
        role. For this test, admin client is used to add roles to alt user,
        which performs API calls, to avoid 401 Unauthorized errors.
        """
        alt_user_id = self.os_alt.credentials.user_id

        def _create_user_domain_role_for_alt_user():
            domain_id = self.setup_test_domain()['id']
            role_id = self.setup_test_role()['id']

            # Create a role association between the user and domain.
            self.roles_client.create_user_role_on_domain(
                domain_id, alt_user_id, role_id)
            self.addCleanup(
                self.roles_client.delete_role_from_user_on_domain,
                domain_id, alt_user_id, role_id)

            return domain_id

        def _create_group_domain_role_for_alt_user():
            domain_id = self.setup_test_domain()['id']
            role_id = self.setup_test_role()['id']

            # Create a group.
            group_id = self.setup_test_group(domain_id=domain_id)['id']

            # Add the alt user to the group.
            self.groups_client.add_group_user(group_id, alt_user_id)
            self.addCleanup(self.groups_client.delete_group_user,
                            group_id, alt_user_id)

            # Create a role association between the group and domain.
            self.roles_client.create_group_role_on_domain(
                domain_id, group_id, role_id)
            self.addCleanup(
                self.roles_client.delete_role_from_group_on_domain,
                domain_id, group_id, role_id)

            return domain_id

        # Add the alt user to 2 random domains and 2 random groups
        # with randomized domains and roles.
        assigned_domain_ids = []
        for _ in range(2):
            domain_id = _create_user_domain_role_for_alt_user()
            assigned_domain_ids.append(domain_id)
            domain_id = _create_group_domain_role_for_alt_user()
            assigned_domain_ids.append(domain_id)

        # Get available domain scopes for the alt user.
        available_domains = self.os_alt.identity_v3_client.list_auth_domains()[
            'domains']
        fetched_domain_ids = [i['id'] for i in available_domains]

        # Verify the expected domain IDs are in the list.
        missing_domain_ids = \
            [p for p in assigned_domain_ids if p not in fetched_domain_ids]
        self.assertEmpty(missing_domain_ids,
                         "Failed to find domain_ids %s in fetched list"
                         % ", ".join(missing_domain_ids))
