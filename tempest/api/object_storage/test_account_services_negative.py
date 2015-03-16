# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

from tempest_lib import exceptions as lib_exc

from tempest.api.object_storage import base
from tempest import clients
from tempest import config
from tempest import test

CONF = config.CONF


class AccountNegativeTest(base.BaseObjectTest):

    @classmethod
    def setup_credentials(cls):
        super(AccountNegativeTest, cls).setup_credentials()
        cls.os_operator = clients.Manager(
            cls.isolated_creds.get_creds_by_roles(
                roles=[CONF.object_storage.operator_role], force_new=True))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('070e6aca-6152-4867-868d-1118d68fb38c')
    def test_list_containers_with_non_authorized_user(self):
        # list containers using non-authorized user

        test_auth_provider = self.os_operator.auth_provider
        # Get auth for the test user
        test_auth_provider.auth_data

        # Get fresh auth for test user and set it to next auth request for
        # account_client
        delattr(test_auth_provider, 'auth_data')
        test_auth_new_data = test_auth_provider.auth_data
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=test_auth_new_data
        )

        params = {'format': 'json'}
        # list containers with non-authorized user token
        self.assertRaises(lib_exc.Forbidden,
                          self.account_client.list_account_containers,
                          params=params)
