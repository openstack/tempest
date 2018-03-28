# Copyright 2015 NEC Corporation. All rights reserved.
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

from tempest.api.compute import base
from tempest.common import utils
from tempest.lib import decorators


class ComputeTenantNetworksTest(base.BaseV2ComputeTest):
    max_microversion = '2.35'

    @classmethod
    def resource_setup(cls):
        super(ComputeTenantNetworksTest, cls).resource_setup()
        cls.client = cls.os_primary.tenant_networks_client
        cls.network = cls.get_tenant_network()

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True)
        super(ComputeTenantNetworksTest, cls).setup_credentials()

    @decorators.idempotent_id('edfea98e-bbe3-4c7a-9739-87b986baff26')
    @utils.services('network')
    def test_list_show_tenant_networks(self):
        # Fetch all networks that are visible to the tenant: this may include
        # shared and external networks
        tenant_networks = [
            n['id'] for n in self.client.list_tenant_networks()['networks']
        ]
        self.assertIn(self.network['id'], tenant_networks,
                      "No tenant networks found.")

        net = self.client.show_tenant_network(self.network['id'])
        self.assertEqual(self.network['id'], net['network']['id'])
