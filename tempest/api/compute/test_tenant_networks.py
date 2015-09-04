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
from tempest import test


class ComputeTenantNetworksTest(base.BaseV2ComputeTest):

    @classmethod
    def resource_setup(cls):
        super(ComputeTenantNetworksTest, cls).resource_setup()
        cls.client = cls.os.tenant_networks_client

    @test.idempotent_id('edfea98e-bbe3-4c7a-9739-87b986baff26')
    def test_list_show_tenant_networks(self):
        tenant_networks = self.client.list_tenant_networks()['networks']
        self.assertNotEmpty(tenant_networks, "No tenant networks found.")

        for net in tenant_networks:
            tenant_network = (self.client.show_tenant_network(net['id'])
                              ['network'])
            self.assertEqual(net['id'], tenant_network['id'])
