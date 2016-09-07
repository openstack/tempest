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

from tempest.lib.services.compute import security_group_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSecurityGroupRulesClient(base.BaseServiceTest):

    FAKE_SECURITY_GROUP_RULE = {
        "security_group_rule": {
            "id": "2d021cf1-ce4b-4292-994f-7a785d62a144",
            "ip_range": {
                "cidr": "0.0.0.0/0"
            },
            "parent_group_id": "48700ff3-30b8-4e63-845f-a79c9633e9fb",
            "to_port": 443,
            "ip_protocol": "tcp",
            "group": {},
            "from_port": 443
        }
    }

    def setUp(self):
        super(TestSecurityGroupRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = security_group_rules_client.SecurityGroupRulesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_security_group_rule(self, bytes_body=False):
        req_body = {
            "from_port": "443",
            "ip_protocol": "tcp",
            "to_port": "443",
            "cidr": "0.0.0.0/0",
            "parent_group_id": "48700ff3-30b8-4e63-845f-a79c9633e9fb"
        }
        self.check_service_client_function(
            self.client.create_security_group_rule,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SECURITY_GROUP_RULE,
            to_utf=bytes_body, **req_body)

    def test_create_security_group_rule_with_str_body(self):
        self._test_create_security_group_rule()

    def test_create_security_group_rule_with_bytes_body(self):
        self._test_create_security_group_rule(bytes_body=True)

    def test_delete_security_group_rule(self):
        self.check_service_client_function(
            self.client.delete_security_group_rule,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, group_rule_id='group-id')
