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

import time

import testtools

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions


CONF = config.CONF


class IdentityV3UsersTest(base.BaseIdentityV3Test):

    @classmethod
    def resource_setup(cls):
        super(IdentityV3UsersTest, cls).resource_setup()
        cls.creds = cls.os_primary.credentials
        cls.user_id = cls.creds.user_id

    def _update_password(self, original_password, password):
        self.non_admin_users_client.update_user_password(
            self.user_id,
            password=password,
            original_password=original_password)

        # NOTE(morganfainberg): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure
        # we are passing the second boundary.
        time.sleep(1)

        # check authorization with new password
        self.non_admin_token.auth(user_id=self.user_id, password=password)

        # Reset auth to get a new token with the new password
        self.non_admin_users_client.auth_provider.clear_auth()
        self.non_admin_users_client.auth_provider.credentials.password = (
            password)

    def _restore_password(self, old_pass, new_pass):
        if CONF.identity_feature_enabled.security_compliance:
            # First we need to clear the password history
            unique_count = CONF.identity.user_unique_last_password_count
            for _ in range(unique_count):
                random_pass = data_utils.rand_password()
                self._update_password(
                    original_password=new_pass, password=random_pass)
                new_pass = random_pass

        self._update_password(original_password=new_pass, password=old_pass)
        # Reset auth again to verify the password restore does work.
        # Clear auth restores the original credentials and deletes
        # cached auth data
        self.non_admin_users_client.auth_provider.clear_auth()
        # NOTE(lbragstad): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure we
        # are passing the second boundary before attempting to
        # authenticate.
        time.sleep(1)
        self.non_admin_users_client.auth_provider.set_auth()

    @decorators.idempotent_id('ad71bd23-12ad-426b-bb8b-195d2b635f27')
    def test_user_update_own_password(self):
        old_pass = self.creds.password
        old_token = self.non_admin_client.token
        new_pass = data_utils.rand_password()

        # to change password back. important for use_dynamic_credentials=false
        self.addCleanup(self._restore_password, old_pass, new_pass)

        # user updates own password
        self._update_password(original_password=old_pass, password=new_pass)

        # authorize with old token should lead to IdentityError (404 code)
        self.assertRaises(exceptions.IdentityError,
                          self.non_admin_token.auth,
                          token=old_token)

        # authorize with old password should lead to Unauthorized
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token.auth,
                          user_id=self.user_id,
                          password=old_pass)

    @testtools.skipUnless(CONF.identity_feature_enabled.security_compliance,
                          'Security compliance not available.')
    @decorators.idempotent_id('941784ee-5342-4571-959b-b80dd2cea516')
    def test_password_history_check_self_service_api(self):
        old_pass = self.creds.password
        new_pass1 = data_utils.rand_password()
        new_pass2 = data_utils.rand_password()

        self.addCleanup(self._restore_password, old_pass, new_pass2)

        # Update password
        self._update_password(original_password=old_pass, password=new_pass1)

        if CONF.identity.user_unique_last_password_count > 1:
            # Can not reuse a previously set password
            self.assertRaises(exceptions.BadRequest,
                              self.non_admin_users_client.update_user_password,
                              self.user_id,
                              password=new_pass1,
                              original_password=new_pass1)

            self.assertRaises(exceptions.BadRequest,
                              self.non_admin_users_client.update_user_password,
                              self.user_id,
                              password=old_pass,
                              original_password=new_pass1)

        # A different password can be set
        self._update_password(original_password=new_pass1, password=new_pass2)

    @testtools.skipUnless(CONF.identity_feature_enabled.security_compliance,
                          'Security compliance not available.')
    @decorators.idempotent_id('a7ad8bbf-2cff-4520-8c1d-96332e151658')
    def test_user_account_lockout(self):
        if (CONF.identity.user_lockout_failure_attempts <= 0 or
                CONF.identity.user_lockout_duration <= 0):
            raise self.skipException(
                "Both CONF.identity.user_lockout_failure_attempts and "
                "CONF.identity.user_lockout_duration should be greater than "
                "zero to test this feature")

        password = self.creds.password

        # First, we login using the correct credentials
        self.non_admin_token.auth(user_id=self.user_id, password=password)

        # Lock user account by using the wrong password to login
        bad_password = data_utils.rand_password()
        for _ in range(CONF.identity.user_lockout_failure_attempts):
            self.assertRaises(exceptions.Unauthorized,
                              self.non_admin_token.auth,
                              user_id=self.user_id,
                              password=bad_password)

        # The user account must be locked, so now it is not possible to login
        # even using the correct password
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token.auth,
                          user_id=self.user_id,
                          password=password)

        # If we wait the required time, the user account will be unlocked
        time.sleep(CONF.identity.user_lockout_duration + 1)
        self.non_admin_token.auth(user_id=self.user_id, password=password)
