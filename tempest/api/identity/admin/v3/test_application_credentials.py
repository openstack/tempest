# Copyright 2018 SUSE Linux GmbH
#
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


class ApplicationCredentialsV3AdminTest(base.BaseApplicationCredentialsV3Test,
                                        base.BaseIdentityV3AdminTest):
    """Test keystone application credentials"""

    @decorators.idempotent_id('3b3dd48f-3388-406a-a9e6-4d078a552d0e')
    def test_create_application_credential_with_roles(self):
        """Test creating keystone application credential with roles"""
        role = self.setup_test_role()
        self.os_admin.roles_v3_client.create_user_role_on_project(
            self.project_id,
            self.user_id,
            role['id']
        )

        app_cred = self.create_application_credential(
            roles=[{'id': role['id']}])
        secret = app_cred['secret']

        # Check that the application credential is functional
        _, resp = self.non_admin_token.get_token(
            app_cred_id=app_cred['id'],
            app_cred_secret=secret,
            auth_data=True
        )
        self.assertEqual(resp['project']['id'], self.project_id)
        self.assertEqual(resp['roles'][0]['id'], role['id'])
