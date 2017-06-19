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

from tempest.lib.services.network import metering_label_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestMeteringLabelRulesClient(base.BaseServiceTest):

    FAKE_METERING_LABEL_RULES = {
        "metering_label_rules": [
            {
                "remote_ip_prefix": "20.0.0.0/24",
                "direction": "ingress",
                "metering_label_id": "e131d186-b02d-4c0b-83d5-0c0725c4f812",
                "id": "9536641a-7d14-4dc5-afaf-93a973ce0eb8",
                "excluded": False
            },
            {
                "remote_ip_prefix": "10.0.0.0/24",
                "direction": "ingress",
                "metering_label_id": "e131d186-b02d-4c0b-83d5-0c0725c4f812",
                "id": "ffc6fd15-40de-4e7d-b617-34d3f7a93aec",
                "excluded": False
            }
        ]
    }

    FAKE_METERING_LABEL_RULE = {
        "remote_ip_prefix": "20.0.0.0/24",
        "direction": "ingress",
        "metering_label_id": "e131d186-b02d-4c0b-83d5-0c0725c4f812"
    }

    FAKE_METERING_LABEL_ID = "e131d186-b02d-4c0b-83d5-0c0725c4f812"
    FAKE_METERING_LABEL_RULE_ID = "9536641a-7d14-4dc5-afaf-93a973ce0eb8"

    def setUp(self):
        super(TestMeteringLabelRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.metering_label_rules_client = \
            metering_label_rules_client.MeteringLabelRulesClient(
                fake_auth, "network", "regionOne")

    def _test_list_metering_label_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_label_rules_client.list_metering_label_rules,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_METERING_LABEL_RULES,
            bytes_body,
            200)

    def _test_create_metering_label_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_label_rules_client.create_metering_label_rule,
            "tempest.lib.common.rest_client.RestClient.post",
            {"metering_label_rule": self.FAKE_METERING_LABEL_RULES[
                "metering_label_rules"][0]},
            bytes_body,
            201,
            **self.FAKE_METERING_LABEL_RULE)

    def _test_show_metering_label_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.metering_label_rules_client.show_metering_label_rule,
            "tempest.lib.common.rest_client.RestClient.get",
            {"metering_label_rule": self.FAKE_METERING_LABEL_RULES[
                "metering_label_rules"][0]},
            bytes_body,
            200,
            metering_label_rule_id=self.FAKE_METERING_LABEL_RULE_ID)

    def test_delete_metering_label_rule(self):
        self.check_service_client_function(
            self.metering_label_rules_client.delete_metering_label_rule,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            metering_label_rule_id=self.FAKE_METERING_LABEL_RULE_ID)

    def test_list_metering_label_rules_with_str_body(self):
        self._test_list_metering_label_rules()

    def test_list_metering_label_rules_with_bytes_body(self):
        self._test_list_metering_label_rules(bytes_body=True)

    def test_create_metering_label_rule_with_str_body(self):
        self._test_create_metering_label_rule()

    def test_create_metering_label_rule_with_bytes_body(self):
        self._test_create_metering_label_rule(bytes_body=True)

    def test_show_metering_label_rule_with_str_body(self):
        self._test_show_metering_label_rule()

    def test_show_metering_label_rule_with_bytes_body(self):
        self._test_show_metering_label_rule(bytes_body=True)
