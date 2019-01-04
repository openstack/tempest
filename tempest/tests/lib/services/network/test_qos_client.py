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

from tempest.lib.services.network import qos_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestQosClient(base.BaseServiceTest):

    FAKE_QOS_POLICY_ID = "f1011b08-1297-11e9-a1e7-c7e6825a2616"

    FAKE_QOS_POLICY_REQUEST = {
        'name': 'foo',
        'shared': True
    }

    FAKE_QOS_POLICY_RESPONSE = {
        'policy': {
            "name": "10Mbit",
            "description": "This policy limits the ports to 10Mbit max.",
            "rules": [],
            "id": FAKE_QOS_POLICY_ID,
            "is_default": False,
            "project_id": "8d4c70a21fed4aeba121a1a429ba0d04",
            "revision_number": 1,
            "tenant_id": "8d4c70a21fed4aeba121a1a429ba0d04",
            "created_at": "2018-04-03T21:26:39Z",
            "updated_at": "2018-04-03T21:26:39Z",
            "shared": False,
            "tags": ["tag1,tag2"]
        }
    }

    FAKE_QOS_POLICIES = {
        'policies': [
            FAKE_QOS_POLICY_RESPONSE['policy']
        ]
    }

    def setUp(self):
        super(TestQosClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.qos_client = qos_client.QosClient(
            fake_auth, "network", "regionOne")

    def _test_create_qos_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_client.create_qos_policy,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_QOS_POLICY_RESPONSE,
            bytes_body,
            201,
            **self.FAKE_QOS_POLICY_REQUEST)

    def _test_list_qos_policies(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_client.list_qos_policies,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_QOS_POLICIES,
            bytes_body,
            200)

    def _test_show_qos_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.qos_client.show_qos_policy,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_QOS_POLICY_RESPONSE,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID)

    def _test_update_qos_polcy(self, bytes_body=False):
        update_kwargs = {
            "name": "100Mbit",
            "description": "This policy limits the ports to 100Mbit max.",
            "shared": True
        }

        resp_body = {
            "policy": copy.deepcopy(
                self.FAKE_QOS_POLICY_RESPONSE['policy']
            )
        }
        resp_body["policy"].update(update_kwargs)

        self.check_service_client_function(
            self.qos_client.update_qos_policy,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            qos_policy_id=self.FAKE_QOS_POLICY_ID,
            **update_kwargs)

    def test_create_qos_policy_with_str_body(self):
        self._test_create_qos_policy()

    def test_create_qos_policy_with_bytes_body(self):
        self._test_create_qos_policy(bytes_body=True)

    def test_update_qos_policy_with_str_body(self):
        self._test_update_qos_polcy()

    def test_update_qos_policy_with_bytes_body(self):
        self._test_update_qos_polcy(bytes_body=True)

    def test_show_qos_policy_with_str_body(self):
        self._test_show_qos_policy()

    def test_show_qos_policy_with_bytes_body(self):
        self._test_show_qos_policy(bytes_body=True)

    def test_delete_qos_policy(self):
        self.check_service_client_function(
            self.qos_client.delete_qos_policy,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            qos_policy_id=self.FAKE_QOS_POLICY_ID)

    def test_list_qos_policies_with_str_body(self):
        self._test_list_qos_policies()

    def test_list_qos_policies_with_bytes_body(self):
        self._test_list_qos_policies(bytes_body=True)
