# Copyright (c) 2019 Ericsson
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

from tempest.lib.services.network import qos_minimum_bandwidth_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestQosMinimumBandwidthRulesClient(base.BaseServiceTest):

    FAKE_QOS_POLICY_ID = "f1011b08-1297-11e9-a1e7-c7e6825a2616"
    FAKE_MIN_BW_RULE_ID = "e758c89e-1297-11e9-a6cf-cf46a71e6699"

    FAKE_MIN_BW_RULE_REQUEST = {
        'qos_policy_id': FAKE_QOS_POLICY_ID,
        'min_kbps': 1000,
        'direction': 'ingress'
    }

    FAKE_MIN_BW_RULE_RESPONSE = {
        'minimum_bandwidth_rule': {
            'id': FAKE_MIN_BW_RULE_ID,
            'min_kbps': 10000,
            'direction': 'egress'
        }
    }

    FAKE_MIN_BW_RULES = {
        'bandwidth_limit_rules': [
            FAKE_MIN_BW_RULE_RESPONSE['minimum_bandwidth_rule']
        ]
    }

    def setUp(self):
        super(TestQosMinimumBandwidthRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.qos_min_bw_client = qos_minimum_bandwidth_rules_client.\
            QosMinimumBandwidthRulesClient(fake_auth, "network", "regionOne")

    def _test_create_minimum_bandwidth_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_min_bw_client.create_minimum_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_MIN_BW_RULE_RESPONSE,
            bytes_body,
            201,
            **self.FAKE_MIN_BW_RULE_REQUEST
        )

    def _test_list_minimum_bandwidth_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_min_bw_client.list_minimum_bandwidth_rules,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_MIN_BW_RULES,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID
        )

    def _test_show_minimum_bandwidth_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_min_bw_client.show_minimum_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_MIN_BW_RULE_RESPONSE,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MIN_BW_RULE_ID
        )

    def _test_update_qos_polcy(self, bytes_body=False):
        update_kwargs = {
            "min_kbps": "20000"
        }

        resp_body = {
            "minimum_bandwidth_rule": copy.deepcopy(
                self.FAKE_MIN_BW_RULE_RESPONSE['minimum_bandwidth_rule']
            )
        }
        resp_body["minimum_bandwidth_rule"].update(update_kwargs)

        self.check_service_client_function(
            self.qos_min_bw_client.update_minimum_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MIN_BW_RULE_ID,
            **update_kwargs)

    def test_create_minimum_bandwidth_rule_with_str_body(self):
        self._test_create_minimum_bandwidth_rule()

    def test_create_minimum_bandwidth_rule_with_bytes_body(self):
        self._test_create_minimum_bandwidth_rule(bytes_body=True)

    def test_update_minimum_bandwidth_rule_with_str_body(self):
        self._test_update_qos_polcy()

    def test_update_minimum_bandwidth_rule_with_bytes_body(self):
        self._test_update_qos_polcy(bytes_body=True)

    def test_show_minimum_bandwidth_rule_with_str_body(self):
        self._test_show_minimum_bandwidth_rule()

    def test_show_minimum_bandwidth_rule_with_bytes_body(self):
        self._test_show_minimum_bandwidth_rule(bytes_body=True)

    def test_delete_minimum_bandwidth_rule(self):
        self.check_service_client_function(
            self.qos_min_bw_client.delete_minimum_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MIN_BW_RULE_ID)

    def test_list_minimum_bandwidth_rule_with_str_body(self):
        self._test_list_minimum_bandwidth_rules()

    def test_list_minimum_bandwidth_rule_with_bytes_body(self):
        self._test_list_minimum_bandwidth_rules(bytes_body=True)
