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

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc

from tempest.api.object_storage import base
from tempest import clients
from tempest import config
from tempest import test

CONF = config.CONF


class AccountQuotasNegativeTest(base.BaseObjectTest):

    @classmethod
    def setup_credentials(cls):
        super(AccountQuotasNegativeTest, cls).setup_credentials()
        reseller_admin_role = CONF.object_storage.reseller_admin_role
        if not cls.isolated_creds.is_role_available(reseller_admin_role):
            skip_msg = ("%s skipped because the configured credential provider"
                        " is not able to provide credentials with the %s role "
                        "assigned." % (cls.__name__, reseller_admin_role))
            raise cls.skipException(skip_msg)
        else:
            cls.os_reselleradmin = clients.Manager(
                cls.isolated_creds.get_creds_by_roles(
                    roles=[reseller_admin_role]))

    @classmethod
    def resource_setup(cls):
        super(AccountQuotasNegativeTest, cls).resource_setup()
        cls.container_name = data_utils.rand_name(name="TestContainer")
        cls.container_client.create_container(cls.container_name)

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

        self.os.account_client.request("POST", url="", headers=headers,
                                       body="")

    def tearDown(self):
        # Set the reselleradmin auth in headers for next account_client
        # request
        self.account_client.auth_provider.set_alt_auth_data(
            request_part='headers',
            auth_data=self.reselleradmin_auth_data
        )
        # remove the quota from the container
        headers = {"X-Remove-Account-Meta-Quota-Bytes": "x"}

        self.os.account_client.request("POST", url="", headers=headers,
                                       body="")
        super(AccountQuotasNegativeTest, self).tearDown()

    @classmethod
    def resource_cleanup(cls):
        if hasattr(cls, "container_name"):
            cls.delete_containers([cls.container_name])
        super(AccountQuotasNegativeTest, cls).resource_cleanup()

    @test.attr(type=["negative", "smoke"])
    @test.idempotent_id('d1dc5076-555e-4e6d-9697-28f1fe976324')
    @test.requires_ext(extension='account_quotas', service='object')
    def test_user_modify_quota(self):
        """Test that a user is not able to modify or remove a quota on
        its account.
        """

        # Not able to remove quota
        self.assertRaises(lib_exc.Forbidden,
                          self.account_client.create_account_metadata,
                          {"Quota-Bytes": ""})

        # Not able to modify quota
        self.assertRaises(lib_exc.Forbidden,
                          self.account_client.create_account_metadata,
                          {"Quota-Bytes": "100"})

    @test.attr(type=["negative", "smoke"])
    @decorators.skip_because(bug="1310597")
    @test.idempotent_id('cf9e21f5-3aa4-41b1-9462-28ac550d8d3f')
    @test.requires_ext(extension='account_quotas', service='object')
    def test_upload_large_object(self):
        object_name = data_utils.rand_name(name="TestObject")
        data = data_utils.arbitrary_string(30)
        self.assertRaises(lib_exc.OverLimit,
                          self.object_client.create_object,
                          self.container_name, object_name, data)
