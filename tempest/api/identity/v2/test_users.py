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

import copy
import time

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions
from tempest import manager
from tempest import test


class IdentityUsersTest(base.BaseIdentityV2Test):

    @classmethod
    def resource_setup(cls):
        super(IdentityUsersTest, cls).resource_setup()
        cls.creds = cls.os.credentials
        cls.username = cls.creds.username
        cls.password = cls.creds.password
        cls.tenant_name = cls.creds.tenant_name

    @test.idempotent_id('165859c9-277f-4124-9479-a7d1627b0ca7')
    def test_user_update_own_password(self):
        self.new_creds = copy.copy(self.creds.credentials)
        self.new_creds.password = data_utils.rand_password()
        # we need new non-admin Identity Client with new credentials, since
        # current non_admin_client token will be revoked after updating
        # password
        self.non_admin_users_client_for_cleanup = copy.copy(
            self.non_admin_users_client)
        self.non_admin_users_client_for_cleanup.auth_provider = (
            manager.get_auth_provider(self.new_creds))
        user_id = self.creds.credentials.user_id
        old_pass = self.creds.credentials.password
        new_pass = self.new_creds.password

        # to change password back. important for allow_tenant_isolation = false
        self.addCleanup(
            self.non_admin_users_client_for_cleanup.update_user_own_password,
            user_id, original_password=new_pass, password=old_pass)
        # user updates own password
        self.non_admin_users_client.update_user_own_password(
            user_id, password=new_pass, original_password=old_pass)
        # NOTE(morganfainberg): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure
        # we are passing the second boundary.
        time.sleep(1)

        # check authorization with new password
        self.non_admin_token_client.auth(self.username,
                                         new_pass,
                                         self.tenant_name)

        # authorize with old token should lead to Unauthorized
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token_client.auth_token,
                          self.non_admin_users_client.token)

        # authorize with old password should lead to Unauthorized
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_token_client.auth,
                          self.username,
                          old_pass,
                          self.tenant_name)
