# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest import exceptions
from tempest.test import attr


class AccountNegativeTest(base.BaseObjectTest):

    @attr(type=['negative', 'gate'])
    def test_list_containers_with_non_authorized_user(self):
        # list containers using non-authorized user

        # create user
        self.data.setup_test_user()
        self.token_client.auth(self.data.test_user,
                               self.data.test_password,
                               self.data.test_tenant)
        new_token = \
            self.token_client.get_token(self.data.test_user,
                                        self.data.test_password,
                                        self.data.test_tenant)
        custom_headers = {'X-Auth-Token': new_token}
        params = {'format': 'json'}
        # list containers with non-authorized user token
        self.assertRaises(exceptions.Unauthorized,
                          self.custom_account_client.list_account_containers,
                          params=params, metadata=custom_headers)
        # delete the user which was created
        self.data.teardown_all()
