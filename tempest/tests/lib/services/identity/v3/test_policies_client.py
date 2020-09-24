# Copyright 2016 Red Hat, Inc.
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

from tempest.lib.services.identity.v3 import policies_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestPoliciesClient(base.BaseServiceTest):
    FAKE_CREATE_POLICY = {
        "policy": {
            "blob": "{'foobar_user': 'role:compute-user'}",
            "project_id": "0426ac1e48f642ef9544c2251e07e261",
            "type": "application/json",
            "user_id": "0ffd248c55b443eaac5253b4e9cbf9b5"
            }
        }

    FAKE_POLICY_INFO = {
        "policy": {
            "blob": {
                "foobar_user": [
                    "role:compute-user"
                    ]
                },
            "id": "717273",
            "links": {
                "self": "http://example.com/identity/v3/policies/717273"
                },
            "project_id": "456789",
            "type": "application/json",
            "user_id": "616263"
            }
        }

    FAKE_ENDPOINT_INFO = {
        "endpoints": [
            {
                "id": "1",
                "interface": "public",
                "links": {
                    "self": "http://example.com/identity/v3/endpoints/1"
                },
                "region": "north",
                "service_id": "9242e05f0c23467bbd1cf1f7a6e5e596",
                "url": "http://example.com/identity/"
            },
            {
                "id": "1",
                "interface": "internal",
                "links": {
                    "self": "http://example.com/identity/v3/endpoints/1"
                },
                "region": "south",
                "service_id": "9242e05f0c23467bbd1cf1f7a6e5e596",
                "url": "http://example.com/identity/"
            }
        ],
        "links": {
            "self": "http://exmp.com/identity/v3/OS-ENDPOINT-POLICY/policies/1"
        }
    }

    FAKE_LIST_POLICIES = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/policies"
            },
        "policies": [
            {
                "blob": {
                    "foobar_user": [
                        "role:compute-user"
                        ]
                    },
                "id": "717273",
                "links": {
                    "self": "http://example.com/identity/v3/policies/717273"
                    },
                "project_id": "456789",
                "type": "application/json",
                "user_id": "616263"
                },
            {
                "blob": {
                    "foobar_user": [
                        "role:compute-user"
                        ]
                    },
                "id": "717274",
                "links": {
                    "self": "http://example.com/identity/v3/policies/717274"
                    },
                "project_id": "456789",
                "type": "application/json",
                "user_id": "616263"
                }
            ]
    }
    FAKE_ENDPOINT_ID = "234789"
    FAKE_SERVICE_ID = "556782"
    FAKE_POLICY_ID = "717273"
    FAKE_REGION_ID = "73"

    def setUp(self):
        super(TestPoliciesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = policies_client.PoliciesClient(fake_auth,
                                                     'identity', 'regionOne')

    def _test_create_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_policy,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_POLICY,
            bytes_body,
            status=201)

    def _test_show_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_policy,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_POLICY_INFO,
            bytes_body,
            policy_id="717273")

    def _test_list_policies(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_policies,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_POLICIES,
            bytes_body)

    def _test_update_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_policy,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_POLICY_INFO,
            bytes_body,
            policy_id="717273")

    def test_create_policy_with_str_body(self):
        self._test_create_policy()

    def test_create_policy_with_bytes_body(self):
        self._test_create_policy(bytes_body=True)

    def test_show_policy_with_str_body(self):
        self._test_show_policy()

    def test_show_policy_with_bytes_body(self):
        self._test_show_policy(bytes_body=True)

    def test_list_policies_with_str_body(self):
        self._test_list_policies()

    def test_list_policies_with_bytes_body(self):
        self._test_list_policies(bytes_body=True)

    def test_update_policy_with_str_body(self):
        self._test_update_policy()

    def test_update_policy_with_bytes_body(self):
        self._test_update_policy(bytes_body=True)

    def test_delete_policy(self):
        self.check_service_client_function(
            self.client.delete_policy,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            policy_id="717273",
            status=204)

    def test_update_policy_association_for_endpoint(self):
        self.check_service_client_function(
            self.client.update_policy_association_for_endpoint,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            policy_id=self.FAKE_POLICY_ID,
            endpoint_id=self.FAKE_ENDPOINT_ID,
            status=204)

    def test_show_policy_association_for_endpoint(self):
        self.check_service_client_function(
            self.client.show_policy_association_for_endpoint,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            policy_id=self.FAKE_POLICY_ID,
            endpoint_id=self.FAKE_ENDPOINT_ID,
            status=204)

    def test_delete_policy_association_for_endpoint(self):
        self.check_service_client_function(
            self.client.delete_policy_association_for_endpoint,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            policy_id=self.FAKE_POLICY_ID,
            endpoint_id=self.FAKE_ENDPOINT_ID,
            status=204)

    def test_update_policy_association_for_service(self):
        self.check_service_client_function(
            self.client.update_policy_association_for_service,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            status=204)

    def test_show_policy_association_for_service(self):
        self.check_service_client_function(
            self.client.show_policy_association_for_service,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            status=204)

    def test_delete_policy_association_for_service(self):
        self.check_service_client_function(
            self.client.delete_policy_association_for_service,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            status=204)

    def test_update_policy_association_for_region_and_service(self):
        self.check_service_client_function(
            self.client.update_policy_association_for_region_and_service,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            region_id=self.FAKE_REGION_ID,
            status=204)

    def test_show_policy_association_for_region_and_service(self):
        self.check_service_client_function(
            self.client.show_policy_association_for_region_and_service,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            region_id=self.FAKE_REGION_ID,
            status=204)

    def test_delete_policy_association_for_region_and_service(self):
        self.check_service_client_function(
            self.client.delete_policy_association_for_region_and_service,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            policy_id=self.FAKE_POLICY_ID,
            service_id=self.FAKE_SERVICE_ID,
            region_id=self.FAKE_REGION_ID,
            status=204)

    def _test_list_endpoints_for_policy(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoints_for_policy,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ENDPOINT_INFO,
            bytes_body,
            policy_id=self.FAKE_POLICY_ID,
            status=200)

    def test_list_endpoints_for_policy_with_str_body(self):
        self._test_list_endpoints_for_policy()

    def test_list_endpoints_for_policy_with_bytes_body(self):
        self._test_list_endpoints_for_policy(bytes_body=True)

    def _test_list_policy_for_endpoint(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_policy_for_endpoint,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_POLICY_INFO,
            bytes_body,
            endpoint_id=self.FAKE_ENDPOINT_ID,
            status=200)

    def test_list_policy_for_endpoint_with_str_body(self):
        self._test_list_policy_for_endpoint()

    def test_list_policy_for_endpoint_with_bytes_body(self):
        self._test_list_policy_for_endpoint(bytes_body=True)
