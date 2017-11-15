# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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

from tempest.api.object_storage import base
from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class AccountQuotasNegativeTest(base.BaseObjectTest):

    credentials = [['operator', CONF.object_storage.operator_role],
                   ['reseller', CONF.object_storage.reseller_admin_role]]

    @classmethod
    def setup_credentials(cls):
        super(AccountQuotasNegativeTest, cls).setup_credentials()
        cls.os_reselleradmin = cls.os_roles_reseller

    @classmethod
    def resource_setup(cls):
        super(AccountQuotasNegativeTest, cls).resource_setup()
        cls.create_container()

        # Retrieve a ResellerAdmin auth data and use it to set a quota
        # on the client's account
        cls.reselleradmin_auth_data = \
            cls.os_reselleradmin.auth_provider.auth_data

    def setUp(self):
        super(AccountQuotasNegativeTest, self).setUp()
        # Set the reselleradmin auth in headers for next account_client
        # request
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.reselleradmin_auth_data
        )
        # Set a quota of 20 bytes on the user's account before each test
        headers = {"X-Account-Meta-Quota-Bytes": "20"}

        self.os_roles_operator.account_client.request(
            "POST", url="", headers=headers, body="")

    def tearDown(self):
        # Set the reselleradmin auth in headers for next account_client
        # request
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.reselleradmin_auth_data
        )
        # remove the quota from the container
        headers = {"X-Remove-Account-Meta-Quota-Bytes": "x"}

        self.os_roles_operator.account_client.request(
            "POST", url="", headers=headers, body="")
        super(AccountQuotasNegativeTest, self).tearDown()

    @classmethod
    def resource_cleanup(cls):
        cls.delete_containers()
        super(AccountQuotasNegativeTest, cls).resource_cleanup()

    @decorators.attr(type=["negative"])
    @decorators.idempotent_id('d1dc5076-555e-4e6d-9697-28f1fe976324')
    @utils.requires_ext(extension='account_quotas', service='object')
    def test_user_modify_quota(self):
        """Test that a user cannot modify or remove a quota on its account."""

        # Not able to remove quota
        self.assertRaises(
            lib_exc.Forbidden,
            self.account_client.create_update_or_delete_account_metadata,
            create_update_metadata={"Quota-Bytes": ""})

        # Not able to modify quota
        self.assertRaises(
            lib_exc.Forbidden,
            self.account_client.create_update_or_delete_account_metadata,
            create_update_metadata={"Quota-Bytes": "100"})
