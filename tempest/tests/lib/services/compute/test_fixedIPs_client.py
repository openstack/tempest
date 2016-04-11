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

from tempest.lib.services.compute import fixed_ips_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestFixedIPsClient(base.BaseComputeServiceTest):
    FIXED_IP_INFO = {"fixed_ip": {"address": "10.0.0.1",
                                  "cidr": "10.11.12.0/24",
                                  "host": "localhost",
                                  "hostname": "OpenStack"}}

    def setUp(self):
        super(TestFixedIPsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.fixedIPsClient = (fixed_ips_client.
                               FixedIPsClient
                               (fake_auth, 'compute',
                                'regionOne'))

    def _test_show_fixed_ip(self, bytes_body=False):
        self.check_service_client_function(
            self.fixedIPsClient.show_fixed_ip,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FIXED_IP_INFO, bytes_body,
            status=200, fixed_ip='Identifier')

    def test_show_fixed_ip_with_str_body(self):
        self._test_show_fixed_ip()

    def test_show_fixed_ip_with_bytes_body(self):
        self._test_show_fixed_ip(True)

    def _test_reserve_fixed_ip(self, bytes_body=False):
        self.check_service_client_function(
            self.fixedIPsClient.reserve_fixed_ip,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, bytes_body,
            status=202, fixed_ip='Identifier')

    def test_reserve_fixed_ip_with_str_body(self):
        self._test_reserve_fixed_ip()

    def test_reserve_fixed_ip_with_bytes_body(self):
        self._test_reserve_fixed_ip(True)
