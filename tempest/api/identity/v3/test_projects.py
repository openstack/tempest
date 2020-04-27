# Copyright 2015 OpenStack Foundation
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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class IdentityV3ProjectsTest(base.BaseIdentityV3Test):
    """Test identity projects"""

    credentials = ['primary', 'alt']

    @decorators.idempotent_id('86128d46-e170-4644-866a-cc487f699e1d')
    def test_list_projects_returns_only_authorized_projects(self):
        """Test listing projects only returns authorized projects"""
        alt_project_name = self.os_alt.credentials.project_name
        resp = self.non_admin_users_client.list_user_projects(
            self.os_primary.credentials.user_id)

        # check that user can see only that projects that he presents in so
        # user can successfully authenticate using his credentials and
        # project name from received projects list
        for project in resp['projects']:
            # 'user_domain_id' needs to be specified otherwise tempest.lib
            # assumes it to be 'default'
            token_id, body = self.non_admin_token.get_token(
                username=self.os_primary.credentials.username,
                user_domain_id=self.os_primary.credentials.user_domain_id,
                password=self.os_primary.credentials.password,
                project_name=project['name'],
                project_domain_id=project['domain_id'],
                auth_data=True)
            self.assertNotEmpty(token_id)
            self.assertEqual(body['project']['id'], project['id'])
            self.assertEqual(body['project']['name'], project['name'])
            self.assertEqual(
                body['user']['id'], self.os_primary.credentials.user_id)

        # check that user cannot log in to alt user's project
        self.assertRaises(
            lib_exc.Unauthorized,
            self.non_admin_token.get_token,
            username=self.os_primary.credentials.username,
            user_domain_id=self.os_primary.credentials.user_domain_id,
            password=self.os_primary.credentials.password,
            project_name=alt_project_name,
            project_domain_id=project['domain_id'])
