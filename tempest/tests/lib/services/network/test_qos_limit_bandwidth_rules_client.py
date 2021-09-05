# Copyright 2021 Red Hat.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import copy

from tempest.lib import decorators

from tempest.lib.services.network import qos_limit_bandwidth_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base

from oslo_log import log as logging
LOG = logging.getLogger('tempest')


class TestQosLimitBandwidthRulesClient(base.BaseServiceTest):

    FAKE_QOS_POLICY_ID = "f1011b08-1297-11e9-a1e7-c7e6825a2616"
    FAKE_MAX_BW_RULE_ID = "e758c89e-1297-11e9-a6cf-cf46a71e6699"

    FAKE_MAX_BW_RULE_REQUEST = {
        'qos_policy_id': FAKE_QOS_POLICY_ID,
        'max_kbps': 1000,
        'max_burst_kbps': 0,
        'direction': 'ingress'
    }

    FAKE_MAX_BW_RULE_RESPONSE = {
        'bandwidth_limit_rule': {
            'id': FAKE_MAX_BW_RULE_ID,
            'max_kbps': 10000,
            'max_burst_kbps': 0,
            'direction': 'ingress'
        }
    }

    FAKE_MAX_BW_RULES = {
        'bandwidth_limit_rules': [
            FAKE_MAX_BW_RULE_RESPONSE['bandwidth_limit_rule']
        ]
    }

    def setUp(self):
        super(TestQosLimitBandwidthRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.qos_limit_bw_client = qos_limit_bandwidth_rules_client.\
            QosLimitBandwidthRulesClient(fake_auth, "network", "regionOne")

    @decorators.idempotent_id('cde981fa-e93b-11eb-aacb-74e5f9e2a801')
    def test_create_limit_bandwidth_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_limit_bw_client.create_limit_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_MAX_BW_RULE_RESPONSE,
            bytes_body,
            201,
            **self.FAKE_MAX_BW_RULE_REQUEST
        )

    @decorators.idempotent_id('86e6803a-e974-11eb-aacb-74e5f9e2a801')
    def test_update_limit_bandwidth_rules(self, bytes_body=False):
        update_kwargs = {
            "max_kbps": "20000"
        }

        resp_body = {
            "bandwidth_limit_rule": copy.deepcopy(
                self.FAKE_MAX_BW_RULE_RESPONSE['bandwidth_limit_rule']
            )
        }
        resp_body["bandwidth_limit_rule"].update(update_kwargs)

        self.check_service_client_function(
            self.qos_limit_bw_client.update_limit_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MAX_BW_RULE_ID,
            **update_kwargs)

    @decorators.idempotent_id('be60ae6e-e979-11eb-aacb-74e5f9e2a801')
    def test_show_limit_bandwidth_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_limit_bw_client.show_limit_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_MAX_BW_RULE_RESPONSE,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MAX_BW_RULE_ID
        )

    @decorators.idempotent_id('0a7c0964-e97b-11eb-aacb-74e5f9e2a801')
    def test_delete_limit_bandwidth_rule(self):
        self.check_service_client_function(
            self.qos_limit_bw_client.delete_limit_bandwidth_rule,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            rule_id=self.FAKE_MAX_BW_RULE_ID)

    @decorators.idempotent_id('08df88ae-e97d-11eb-aacb-74e5f9e2a801')
    def test_list_minimum_bandwidth_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_limit_bw_client.list_limit_bandwidth_rules,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_MAX_BW_RULES,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID
        )
