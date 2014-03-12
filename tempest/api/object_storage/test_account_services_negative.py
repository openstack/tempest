# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
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

from tempest.api.object_storage import base
from tempest import clients
from tempest import exceptions
from tempest.test import attr


class AccountNegativeTest(base.BaseObjectTest):

    @attr(type=['negative', 'gate'])
    def test_list_containers_with_non_authorized_user(self):
        # list containers using non-authorized user

        # create user
        self.data.setup_test_user()
        test_os = clients.Manager(self.data.test_user,
                                  self.data.test_password,
                                  self.data.test_tenant)
        test_auth_provider = test_os.auth_provider
        # Get auth for the test user
        test_auth_provider.auth_data

        # Get fresh auth for test user and set it to next auth request for
        # custom_account_client
        delattr(test_auth_provider, 'auth_data')
        test_auth_new_data = test_auth_provider.auth_data
        self.custom_account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=test_auth_new_data
        )

        params = {'format': 'json'}
        # list containers with non-authorized user token
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_account_client.list_account_containers,
                          params=params)
        # delete the user which was created
        self.data.teardown_all()
