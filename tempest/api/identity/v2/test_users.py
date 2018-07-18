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

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions


CONF = config.CONF


class IdentityUsersTest(base.BaseIdentityV2Test):

    @classmethod
    def resource_setup(cls):
        super(IdentityUsersTest, cls).resource_setup()
        cls.creds = cls.os_primary.credentials
        cls.username = cls.creds.username
        cls.password = cls.creds.password
        cls.tenant_name = cls.creds.tenant_name

    def _update_password(self, user_id, original_password, password):
        self.non_admin_users_client.update_user_own_password(
            user_id, password=password, original_password=original_password)

        # NOTE(morganfainberg): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure
        # we are passing the second boundary.
        time.sleep(1)

        # check authorization with new password
        self.non_admin_token_client.auth(self.username,
                                         password,
                                         self.tenant_name)

        # Reset auth to get a new token with the new password
        self.non_admin_users_client.auth_provider.clear_auth()
        self.non_admin_users_client.auth_provider.credentials.password = (
            password)

    def _restore_password(self, user_id, old_pass, new_pass):
        if CONF.identity_feature_enabled.security_compliance:
            # First we need to clear the password history
            unique_count = CONF.identity.user_unique_last_password_count
            for _ in range(unique_count):
                random_pass = data_utils.rand_password()
                self._update_password(
                    user_id, original_password=new_pass, password=random_pass)
                new_pass = random_pass

        self._update_password(
            user_id, original_password=new_pass, password=old_pass)
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

    @decorators.idempotent_id('165859c9-277f-4124-9479-a7d1627b0ca7')
    def test_user_update_own_password(self):
        old_pass = self.creds.password
        old_token = self.non_admin_users_client.token
        new_pass = data_utils.rand_password()
        user_id = self.creds.user_id

        # to change password back. important for use_dynamic_credentials=false
        self.addCleanup(self._restore_password, user_id, old_pass, new_pass)

        # user updates own password
        self._update_password(
            user_id, original_password=old_pass, password=new_pass)

        # authorize with old token should lead to Unauthorized
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token_client.auth_token,
                          old_token)

        # authorize with old password should lead to Unauthorized
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token_client.auth,
                          self.username,
                          old_pass,
                          self.tenant_name)
