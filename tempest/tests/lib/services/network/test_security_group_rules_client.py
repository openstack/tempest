# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

import copy

import mock
from oslo_serialization import jsonutils as json

from tempest.lib.services.network import base as network_base
from tempest.lib.services.network import security_group_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSecurityGroupsClient(base.BaseServiceTest):

    FAKE_SEC_GROUP_RULE_ID = "3c0e45ff-adaf-4124-b083-bf390e5482ff"

    FAKE_SECURITY_GROUP_RULES = {
        "security_group_rules": [
            {
                "direction": "egress",
                "ethertype": "IPv6",
                "id": "3c0e45ff-adaf-4124-b083-bf390e5482ff",
                "port_range_max": None,
                "port_range_min": None,
                "protocol": None,
                "remote_group_id": None,
                "remote_ip_prefix": None,
                "security_group_id": "85cc3048-abc3-43cc-89b3-377341426ac5",
                "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                "description": ""
            },
            {
                "direction": "egress",
                "ethertype": "IPv4",
                "id": "93aa42e5-80db-4581-9391-3a608bd0e448",
                "port_range_max": None,
                "port_range_min": None,
                "protocol": None,
                "remote_group_id": None,
                "remote_ip_prefix": None,
                "security_group_id": "85cc3048-abc3-43cc-89b3-377341426ac5",
                "project_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                "tenant_id": "e4f50856753b4dc6afee5fa6b9b6c550",
                "description": ""
            }
        ]
    }

    FAKE_SECURITY_GROUP_RULE = copy.copy(
        FAKE_SECURITY_GROUP_RULES['security_group_rules'][0])

    def setUp(self):
        super(TestSecurityGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = security_group_rules_client.SecurityGroupRulesClient(
            fake_auth, 'network', 'regionOne')

    def _test_list_security_group_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_security_group_rules,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SECURITY_GROUP_RULES,
            bytes_body,
            mock_args='v2.0/security-group-rules')

    def _test_create_security_group_rule(self, bytes_body=False):
        kwargs = {'direction': 'egress',
                  'security_group_id': '85cc3048-abc3-43cc-89b3-377341426ac5',
                  'remote_ip_prefix': None}
        payload = json.dumps({"security_group_rule": kwargs}, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(network_base.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.create_security_group_rule,
                'tempest.lib.common.rest_client.RestClient.post',
                self.FAKE_SECURITY_GROUP_RULE,
                bytes_body,
                status=201,
                mock_args=['v2.0/security-group-rules', payload],
                **kwargs)

    def _test_show_security_group_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_security_group_rule,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SECURITY_GROUP_RULE,
            bytes_body,
            security_group_rule_id=self.FAKE_SEC_GROUP_RULE_ID,
            mock_args='v2.0/security-group-rules/%s'
                      % self.FAKE_SEC_GROUP_RULE_ID)

    def test_list_security_group_rules_with_str_body(self):
        self._test_list_security_group_rules()

    def test_list_security_group_rules_with_bytes_body(self):
        self._test_list_security_group_rules(bytes_body=True)

    def test_create_security_group_rule_with_str_body(self):
        self._test_create_security_group_rule()

    def test_create_security_group_rule_with_bytes_body(self):
        self._test_create_security_group_rule(bytes_body=True)

    def test_show_security_group_rule_with_str_body(self):
        self._test_show_security_group_rule()

    def test_show_security_group_rule_with_bytes_body(self):
        self._test_show_security_group_rule(bytes_body=True)

    def test_delete_security_group_rule(self):
        self.check_service_client_function(
            self.client.delete_security_group_rule,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            security_group_rule_id=self.FAKE_SEC_GROUP_RULE_ID,
            mock_args='v2.0/security-group-rules/%s'
                      % self.FAKE_SEC_GROUP_RULE_ID)
