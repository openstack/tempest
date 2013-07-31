# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
#
# Author: Joe H. Rahme <joe.hakim.rahme@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools

from tempest.api.object_storage import base
from tempest import clients
from tempest.common.utils.data_utils import arbitrary_string
from tempest.common.utils.data_utils import rand_name
import tempest.config
from tempest import exceptions
from tempest.test import attr


class AccountQuotasTest(base.BaseObjectTest):
    accounts_quotas_available = \
        tempest.config.TempestConfig().object_storage.accounts_quotas_available

    @classmethod
    def setUpClass(cls):
        super(AccountQuotasTest, cls).setUpClass()
        cls.container_name = rand_name(name="TestContainer")
        cls.container_client.create_container(cls.container_name)

        cls.data.setup_test_user()

        cls.os_reselleradmin = clients.Manager(
            cls.data.test_user,
            cls.data.test_password,
            cls.data.test_tenant)

        # Retrieve the ResellerAdmin role id
        reseller_role_id = None
        try:
            _, roles = cls.os_admin.identity_client.list_roles()
            reseller_role_id = next(r['id'] for r in roles if r['name']
                                    == 'ResellerAdmin')
        except StopIteration:
            msg = "No ResellerAdmin role found"
            raise exceptions.NotFound(msg)

        # Retrieve the ResellerAdmin tenant id
        _, users = cls.os_admin.identity_client.get_users()
        reseller_user_id = next(usr['id'] for usr in users if usr['name']
                                == cls.data.test_user)

        # Retrieve the ResellerAdmin tenant id
        _, tenants = cls.os_admin.identity_client.list_tenants()
        reseller_tenant_id = next(tnt['id'] for tnt in tenants if tnt['name']
                                  == cls.data.test_tenant)

        # Assign the newly created user the appropriate ResellerAdmin role
        cls.os_admin.identity_client.assign_user_role(
            reseller_tenant_id,
            reseller_user_id,
            reseller_role_id)

        # Retrieve a ResellerAdmin auth token and use it to set a quota
        # on the client's account
        cls.reselleradmin_token = cls.token_client.get_token(
            cls.data.test_user,
            cls.data.test_password,
            cls.data.test_tenant)

        headers = {"X-Auth-Token": cls.reselleradmin_token,
                   "X-Account-Meta-Quota-Bytes": "20"}

        cls.os.custom_account_client.request("POST", "", headers, "")

    @classmethod
    def tearDownClass(cls):
        cls.delete_containers([cls.container_name])
        cls.data.teardown_all()

        # remove the quota from the container
        headers = {"X-Auth-Token": cls.reselleradmin_token,
                   "X-Remove-Account-Meta-Quota-Bytes": "x"}

        cls.os.custom_account_client.request("POST", "", headers, "")

        super(AccountQuotasTest, cls).tearDownClass()

    @testtools.skipIf(not accounts_quotas_available,
                      "Account Quotas middleware not available")
    @attr(type="smoke")
    def test_upload_valid_object(self):
        object_name = rand_name(name="TestObject")
        data = arbitrary_string()
        resp, _ = self.object_client.create_object(self.container_name,
                                                   object_name, data)

        self.assertEqual(resp["status"], "201")

    @testtools.skipIf(not accounts_quotas_available,
                      "Account Quotas middleware not available")
    @attr(type=["negative", "smoke"])
    def test_upload_large_object(self):
        object_name = rand_name(name="TestObject")
        data = arbitrary_string(30)
        self.assertRaises(exceptions.OverLimit,
                          self.object_client.create_object,
                          self.container_name, object_name, data)
