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

import datetime

from oslo_utils import timeutils

from tempest.api.identity import base
from tempest.lib import decorators


class ApplicationCredentialsV3Test(base.BaseApplicationCredentialsV3Test):
    """Test application credentials"""

    def _list_app_creds(self, name=None):
        kwargs = dict(user_id=self.user_id)
        if name:
            kwargs.update(name=name)
        return self.non_admin_app_creds_client.list_application_credentials(
            **kwargs)['application_credentials']

    @decorators.idempotent_id('8080c75c-eddc-4786-941a-c2da7039ae61')
    def test_create_application_credential(self):
        """Test creating application credential"""
        app_cred = self.create_application_credential()

        # Check that the secret appears in the create response
        secret = app_cred['secret']

        # Check that the secret is not retrievable after initial create
        app_cred = self.non_admin_app_creds_client.show_application_credential(
            user_id=self.user_id,
            application_credential_id=app_cred['id']
        )['application_credential']
        self.assertNotIn('secret', app_cred)

        # Check that the application credential is functional
        token_id, resp = self.non_admin_token.get_token(
            app_cred_id=app_cred['id'],
            app_cred_secret=secret,
            auth_data=True
        )
        self.assertEqual(resp['project']['id'], self.project_id)

    @decorators.idempotent_id('852daf0c-42b5-4239-8466-d193d0543ed3')
    def test_create_application_credential_expires(self):
        """Test creating application credential with expire time"""
        expires_at = timeutils.utcnow() + datetime.timedelta(hours=1)

        app_cred = self.create_application_credential(expires_at=expires_at)

        expires_str = expires_at.isoformat()
        self.assertEqual(expires_str, app_cred['expires_at'])

    @decorators.idempotent_id('ff0cd457-6224-46e7-b79e-0ada4964a8a6')
    def test_list_application_credentials(self):
        """Test listing application credentials"""
        self.create_application_credential()
        self.create_application_credential()

        app_creds = self._list_app_creds()
        self.assertEqual(2, len(app_creds))

    @decorators.idempotent_id('9bb5e5cc-5250-493a-8869-8b665f6aa5f6')
    def test_query_application_credentials(self):
        """Test listing application credentials filtered by name"""
        self.create_application_credential()
        app_cred_two = self.create_application_credential()
        app_cred_two_name = app_cred_two['name']

        app_creds = self._list_app_creds(name=app_cred_two_name)
        self.assertEqual(1, len(app_creds))
        self.assertEqual(app_cred_two_name, app_creds[0]['name'])
