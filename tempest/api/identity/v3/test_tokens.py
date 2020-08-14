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

import operator

from oslo_utils import timeutils
import six

from tempest.api.identity import base
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class TokensV3Test(base.BaseIdentityV3Test):
    """Test identity tokens"""

    @decorators.idempotent_id('a9512ac3-3909-48a4-b395-11f438e16260')
    def test_validate_token(self):
        """Test validating token for user"""
        creds = self.os_primary.credentials
        user_id = creds.user_id
        username = creds.username
        password = creds.password
        user_domain_id = creds.user_domain_id
        # GET and validate token
        subject_token, token_body = self.non_admin_token.get_token(
            user_id=user_id,
            username=username,
            user_domain_id=user_domain_id,
            password=password,
            auth_data=True)
        authenticated_token = self.non_admin_client.show_token(
            subject_token)['token']
        # sanity checking to make sure they are indeed the same token
        # If there are roles in the token, sort the roles
        authenticated_token_roles = authenticated_token.get("roles")
        if authenticated_token_roles:
            authenticated_token["roles"] = authenticated_token_roles.sort(
                key=operator.itemgetter('id'))
        token_body_roles = token_body.get("roles")
        if token_body_roles:
            token_body["roles"] = token_body_roles.sort(
                key=operator.itemgetter('id'))
        self.assertEqual(authenticated_token, token_body)
        # test to see if token has been properly authenticated
        self.assertEqual(authenticated_token['user']['id'], user_id)
        # NOTE: resource name that are case-sensitive in keystone
        # depends on backends such as MySQL or LDAP which are
        # case-insensitive, case-preserving. Resource name is
        # returned as it is stored in the backend, not as it is
        # requested. Verifying the username with both lower-case to
        # avoid failure on different backends
        self.assertEqual(
            authenticated_token['user']['name'].lower(), username.lower())

        self.non_admin_client.delete_token(subject_token)
        self.assertRaises(
            lib_exc.NotFound, self.non_admin_client.show_token, subject_token)

    @decorators.idempotent_id('6f8e4436-fc96-4282-8122-e41df57197a9')
    def test_create_token(self):
        """Test creating token for user"""
        creds = self.os_primary.credentials
        user_id = creds.user_id
        username = creds.username
        password = creds.password
        user_domain_id = creds.user_domain_id

        # 'user_domain_id' needs to be specified otherwise tempest.lib assumes
        # it to be 'default'
        token_id, resp = self.non_admin_token.get_token(
            user_id=user_id,
            username=username,
            user_domain_id=user_domain_id,
            password=password,
            auth_data=True)

        self.assertNotEmpty(token_id)
        self.assertIsInstance(token_id, six.string_types)

        now = timeutils.utcnow()
        expires_at = timeutils.normalize_time(
            timeutils.parse_isotime(resp['expires_at']))
        self.assertGreater(resp['expires_at'],
                           resp['issued_at'])
        self.assertGreater(expires_at, now)

        subject_id = resp['user']['id']
        if user_id:
            self.assertEqual(subject_id, user_id)
        else:
            # Expect a user ID, but don't know what it will be.
            self.assertIsNotNone(subject_id, 'Expected user ID in token.')

        subject_name = resp['user']['name']

        if username:
            # NOTE: resource name that are case-sensitive in keystone
            # depends on backends such as MySQL or LDAP which are
            # case-insensitive, case-preserving. Resource name is
            # returned as it is stored in the backend, not as it is
            # requested. Verifying the username with both lower-case to
            # avoid failure on different backends
            self.assertEqual(subject_name.lower(), username.lower())
        else:
            # Expect a user name, but don't know what it will be
            self.assertIsNotNone(subject_name, 'Expected user name in token.')

        self.assertEqual(resp['methods'][0], 'password')

    @decorators.idempotent_id('0f9f5a5f-d5cd-4a86-8a5b-c5ded151f212')
    def test_token_auth_creation_existence_deletion(self):
        """Test auth/check existence/delete token for user

        Tests basic token auth functionality in a way that is compatible with
        pre-provisioned credentials. The default user is used for token
        authentication.
        """

        # Valid user's token is authenticated
        user = self.os_primary.credentials
        # Perform Authentication
        resp = self.non_admin_token.auth(
            user_id=user.user_id, password=user.password).response
        subject_token = resp['x-subject-token']
        self.non_admin_client.check_token_existence(subject_token)
        # Perform GET Token
        token_details = self.non_admin_client.show_token(
            subject_token)['token']
        self.assertEqual(resp['x-subject-token'], subject_token)
        self.assertEqual(token_details['user']['id'], user.user_id)
        # NOTE: resource name that are case-sensitive in keystone
        # depends on backends such as MySQL or LDAP which are
        # case-insensitive, case-preserving. Resource name is
        # returned as it is stored in the backend, not as it is
        # requested. Verifying the username with both lower-case to
        # avoid failure on different backends
        self.assertEqual(
            token_details['user']['name'].lower(),
            user.username.lower())
        # Perform Delete Token
        self.non_admin_client.delete_token(subject_token)
        self.assertRaises(lib_exc.NotFound,
                          self.non_admin_client.check_token_existence,
                          subject_token)
