# Copyright 2014 IBM Corp.
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
from tempest import config
from tempest import test

CONF = config.CONF


class NetworksTestJSON(base.BaseV2ComputeTest):
    @classmethod
    def skip_checks(cls):
        super(NetworksTestJSON, cls).skip_checks()
        if CONF.service_available.neutron:
            raise cls.skipException('nova-network is not available.')

    @classmethod
    def setup_clients(cls):
        super(NetworksTestJSON, cls).setup_clients()
        cls.client = cls.os.networks_client

    @test.attr(type='gate')
    @test.idempotent_id('3fe07175-312e-49a5-a623-5f52eeada4c2')
    def test_list_networks(self):
        networks = self.client.list_networks()
        self.assertNotEmpty(networks, "No networks found.")
