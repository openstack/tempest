# Copyright 2013 OpenStack Foundation
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

import time

import testtools

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


CONF = config.CONF


class UsersV3TestJSON(base.BaseIdentityV3AdminTest):
    """Test keystone users"""

    @classmethod
    def skip_checks(cls):
        super(UsersV3TestJSON, cls).skip_checks()
        if CONF.identity_feature_enabled.immutable_user_source:
            raise cls.skipException('Skipped because environment has an '
                                    'immutable user source and solely '
                                    'provides read-only access to users.')

    @decorators.idempotent_id('b537d090-afb9-4519-b95d-270b0708e87e')
    def test_user_update(self):
        """Test case to check if updating of user attributes is successful"""
        # Creating first user
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_password()
        user = self.users_client.create_user(
            name=u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False)['user']
        # Delete the User at the end of this method
        self.addCleanup(self.users_client.delete_user, user['id'])

        # Creating second project for updation
        project = self.setup_test_project()

        # Updating user details with new values
        update_kwargs = {'name': data_utils.rand_name('user2'),
                         'description': data_utils.rand_name('desc2'),
                         'project_id': project['id'],
                         'email': 'user2@testmail.tm',
                         'enabled': False}
        updated_user = self.users_client.update_user(
            user['id'], **update_kwargs)['user']
        for field in update_kwargs:
            self.assertEqual(update_kwargs[field], updated_user[field])

        # GET by id after updating
        new_user_get = self.users_client.show_user(user['id'])['user']
        # Assert response body of GET after updation
        for field in update_kwargs:
            self.assertEqual(update_kwargs[field], new_user_get[field])

    @decorators.idempotent_id('2d223a0e-e457-4a70-9fb1-febe027a0ff9')
    def test_update_user_password(self):
        """Test updating user password"""
        # Creating User to check password updation
        u_name = data_utils.rand_name('user')
        original_password = data_utils.rand_password()
        user = self.users_client.create_user(
            name=u_name, password=original_password)['user']
        # Delete the User at the end all test methods
        self.addCleanup(self.users_client.delete_user, user['id'])
        # Update user with new password
        new_password = data_utils.rand_password()
        self.users_client.update_user_password(
            user['id'], password=new_password,
            original_password=original_password)
        # NOTE(morganfainberg): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure
        # we are passing the second boundary.
        time.sleep(1)
        resp = self.token.auth(user_id=user['id'],
                               password=new_password).response
        subject_token = resp['x-subject-token']
        # Perform GET Token to verify and confirm password is updated
        token_details = self.client.show_token(subject_token)['token']
        self.assertEqual(token_details['user']['id'], user['id'])
        self.assertEqual(token_details['user']['name'], u_name)

    @decorators.idempotent_id('a831e70c-e35b-430b-92ed-81ebbc5437b8')
    def test_list_user_projects(self):
        """Test listing the projects that a user has access upon"""
        assigned_project_ids = list()
        fetched_project_ids = list()
        u_project = self.setup_test_project()
        # Create a user.
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_password()
        user_body = self.users_client.create_user(
            name=u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False, project_id=u_project['id'])['user']
        # Delete the User at the end of this method
        self.addCleanup(self.users_client.delete_user, user_body['id'])
        # Creating Role
        role_body = self.setup_test_role()

        user = self.users_client.show_user(user_body['id'])['user']
        role = self.roles_client.show_role(role_body['id'])['role']
        for _ in range(2):
            # Creating project so as to assign role
            project_body = self.setup_test_project()
            project = self.projects_client.show_project(
                project_body['id'])['project']
            # Assigning roles to user on project
            self.roles_client.create_user_role_on_project(project['id'],
                                                          user['id'],
                                                          role['id'])
            assigned_project_ids.append(project['id'])
        body = self.users_client.list_user_projects(user['id'])['projects']
        for i in body:
            fetched_project_ids.append(i['id'])
        # verifying the project ids in list
        missing_projects =\
            [p for p in assigned_project_ids
             if p not in fetched_project_ids]
        self.assertEmpty(missing_projects,
                         "Failed to find project %s in fetched list" %
                         ', '.join(m_project for m_project
                                   in missing_projects))

    @decorators.idempotent_id('c10dcd90-461d-4b16-8e23-4eb836c00644')
    def test_get_user(self):
        """Test getting a user detail"""
        user = self.setup_test_user()
        fetched_user = self.users_client.show_user(user['id'])['user']
        self.assertEqual(user['id'], fetched_user['id'])

    @testtools.skipUnless(CONF.identity_feature_enabled.security_compliance,
                          'Security compliance not available.')
    @decorators.idempotent_id('568cd46c-ee6c-4ab4-a33a-d3791931979e')
    def test_password_history_not_enforced_in_admin_reset(self):
        """Test setting same password when password history is not enforced"""
        old_password = self.os_primary.credentials.password
        user_id = self.os_primary.credentials.user_id

        new_password = data_utils.rand_password()
        self.users_client.update_user(user_id, password=new_password)
        # To be safe, we add this cleanup to restore the original password in
        # case something goes wrong before it is restored later.
        self.addCleanup(
            self.users_client.update_user, user_id, password=old_password)

        # Check authorization with new password
        self.token.auth(user_id=user_id, password=new_password)

        if CONF.identity.user_unique_last_password_count > 1:
            # The password history is not enforced via the admin reset route.
            # We can set the same password.
            self.users_client.update_user(user_id, password=new_password)

        # Restore original password
        self.users_client.update_user(user_id, password=old_password)
        # Check authorization with old password
        self.token.auth(user_id=user_id, password=old_password)
