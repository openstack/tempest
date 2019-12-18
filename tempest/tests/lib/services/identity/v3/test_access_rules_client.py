# Copyright 2019 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import access_rules_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAccessRulesClient(base.BaseServiceTest):
    FAKE_LIST_ACCESS_RULES = {
        "links": {
            "self": "https://example.com/identity/v3/users/" +
                    "3e0716ae/access_rules",
            "previous": None,
            "next": None
        },
        "access_rules": [
            {
                "path": "/v2.0/metrics",
                "links": {
                    "self": "https://example.com/identity/v3/access_rules/" +
                            "07d719df00f349ef8de77d542edf010c"
                },
                "id": "07d719df00f349ef8de77d542edf010c",
                "service": "monitoring",
                "method": "GET"
            }
        ]
    }

    FAKE_ACCESS_RULE_INFO = {
        "access_rule": {
            "path": "/v2.0/metrics",
            "links": {
                "self": "https://example.com/identity/v3/access_rules/" +
                        "07d719df00f349ef8de77d542edf010c"
            },
            "id": "07d719df00f349ef8de77d542edf010c",
            "service": "monitoring",
            "method": "GET"
        }
    }

    def setUp(self):
        super(TestAccessRulesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = access_rules_client.AccessRulesClient(
            fake_auth, 'identity', 'regionOne')

    def _test_show_access_rule(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_access_rule,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ACCESS_RULE_INFO,
            bytes_body,
            user_id="123456",
            access_rule_id="5499a186")

    def _test_list_access_rules(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_access_rules,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ACCESS_RULES,
            bytes_body,
            user_id="123456")

    def test_show_access_rule_with_str_body(self):
        self._test_show_access_rule()

    def test_show_access_rule_with_bytes_body(self):
        self._test_show_access_rule(bytes_body=True)

    def test_list_access_rule_with_str_body(self):
        self._test_list_access_rules()

    def test_list_access_rule_with_bytes_body(self):
        self._test_list_access_rules(bytes_body=True)

    def test_delete_access_rule(self):
        self.check_service_client_function(
            self.client.delete_access_rule,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id="123456",
            access_rule_id="5499a186",
            status=204)
