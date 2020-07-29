# Copyright 2015 Cloudwatt
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

from tempest.api.network import base
from tempest.common import identity
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class QuotasNegativeTest(base.BaseAdminNetworkTest):
    """Tests the following operations in the Neutron API:

        set network quota and exceed this quota

    v2.0 of the API is assumed.
    It is also assumed that the per-project quota extension API is configured
    in /etc/neutron/neutron.conf as follows:

        quota_driver = neutron.db.quota.driver.DbQuotaDriver
    """

    @classmethod
    def skip_checks(cls):
        super(QuotasNegativeTest, cls).skip_checks()
        if not utils.is_extension_enabled('quotas', 'network'):
            msg = "quotas extension not enabled."
            raise cls.skipException(msg)

    def setUp(self):
        super(QuotasNegativeTest, self).setUp()
        name = data_utils.rand_name('test_project_')
        description = data_utils.rand_name('desc_')
        self.project = identity.identity_utils(self.os_admin).create_project(
            name=name, description=description)
        self.addCleanup(identity.identity_utils(self.os_admin).delete_project,
                        self.project['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('644f4e1b-1bf9-4af0-9fd8-eb56ac0f51cf')
    def test_network_quota_exceeding(self):
        """Test creating network when exceeding network quota will fail"""
        # Set the network quota to two
        self.admin_quotas_client.update_quotas(self.project['id'], network=2)

        # Create two networks
        n1 = self.admin_networks_client.create_network(
            project_id=self.project['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_networks_client.delete_network,
                        n1['network']['id'])
        n2 = self.admin_networks_client.create_network(
            project_id=self.project['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.admin_networks_client.delete_network,
                        n2['network']['id'])

        # Try to create a third network while the quota is two
        with self.assertRaisesRegex(
                lib_exc.Conflict,
                r"Quota exceeded for resources: \['network'\].*"):
            n3 = self.admin_networks_client.create_network(
                project_id=self.project['id'])
            self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                            self.admin_networks_client.delete_network,
                            n3['network']['id'])
