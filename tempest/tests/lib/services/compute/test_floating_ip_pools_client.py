# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.compute import floating_ip_pools_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestFloatingIPPoolsClient(base.BaseComputeServiceTest):

    FAKE_FLOATING_IP_POOLS = {
        "floating_ip_pools":
        [
            {"name": u'\u3042'},
            {"name": u'\u3044'}
        ]
    }

    def setUp(self):
        super(TestFloatingIPPoolsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = floating_ip_pools_client.FloatingIPPoolsClient(
            fake_auth, 'compute', 'regionOne')

    def test_list_floating_ip_pools_with_str_body(self):
        self.check_service_client_function(
            self.client.list_floating_ip_pools,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_FLOATING_IP_POOLS)

    def test_list_floating_ip_pools_with_bytes_body(self):
        self.check_service_client_function(
            self.client.list_floating_ip_pools,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_FLOATING_IP_POOLS, to_utf=True)
