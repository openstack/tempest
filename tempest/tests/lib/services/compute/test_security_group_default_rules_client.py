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

from tempest.lib.services.compute import security_group_default_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestSecurityGroupDefaultRulesClient(base.BaseComputeServiceTest):
    FAKE_RULE = {
        "from_port": 80,
        "id": 1,
        "ip_protocol": "TCP",
        "ip_range": {
            "cidr": "10.10.10.0/24"
        },
        "to_port": 80
    }

    def setUp(self):
        super(TestSecurityGroupDefaultRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = (security_group_default_rules_client.
                       SecurityGroupDefaultRulesClient(fake_auth, 'compute',
                                                       'regionOne'))

    def _test_list_security_group_default_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_security_group_default_rules,
            'tempest.lib.common.rest_client.RestClient.get',
            {"security_group_default_rules": [self.FAKE_RULE]},
            to_utf=bytes_body)

    def test_list_security_group_default_rules_with_str_body(self):
        self._test_list_security_group_default_rules()

    def test_list_security_group_default_rules_with_bytes_body(self):
        self._test_list_security_group_default_rules(bytes_body=True)

    def _test_show_security_group_default_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_security_group_default_rule,
            'tempest.lib.common.rest_client.RestClient.get',
            {"security_group_default_rule": self.FAKE_RULE},
            to_utf=bytes_body,
            security_group_default_rule_id=1)

    def test_show_security_group_default_rule_with_str_body(self):
        self._test_show_security_group_default_rule()

    def test_show_security_group_default_rule_with_bytes_body(self):
        self._test_show_security_group_default_rule(bytes_body=True)

    def _test_create_security_default_group_rule(self, bytes_body=False):
        request_body = {
            "to_port": 80,
            "from_port": 80,
            "ip_protocol": "TCP",
            "cidr": "10.10.10.0/24"
        }
        self.check_service_client_function(
            self.client.create_security_default_group_rule,
            'tempest.lib.common.rest_client.RestClient.post',
            {"security_group_default_rule": self.FAKE_RULE},
            to_utf=bytes_body, **request_body)

    def test_create_security_default_group_rule_with_str_body(self):
        self._test_create_security_default_group_rule()

    def test_create_security_default_group_rule_with_bytes_body(self):
        self._test_create_security_default_group_rule(bytes_body=True)

    def test_delete_security_group_default_rule(self):
        self.check_service_client_function(
            self.client.delete_security_group_default_rule,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=204, security_group_default_rule_id=1)
