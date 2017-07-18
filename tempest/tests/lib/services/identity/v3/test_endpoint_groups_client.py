# Copyright 2017 AT&T Corporation.
# All Rights Reserved.
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

from tempest.lib.services.identity.v3 import endpoint_groups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestEndPointGroupsClient(base.BaseServiceTest):
    FAKE_CREATE_ENDPOINT_GROUP = {
        "endpoint_group": {
            "id": 1,
            "name": "FAKE_ENDPOINT_GROUP",
            "description": "FAKE SERVICE ENDPOINT GROUP",
            "filters": {
                "service_id": 1
            }
        }
    }

    FAKE_ENDPOINT_GROUP_INFO = {
        "endpoint_group": {
            "id": 1,
            "name": "FAKE_ENDPOINT_GROUP",
            "description": "FAKE SERVICE ENDPOINT GROUP",
            "links": {
                "self": "http://example.com/identity/v3/OS-EP-FILTER/" +
                        "endpoint_groups/1"
            },
            "filters": {
                "service_id": 1
            }
        }
    }

    FAKE_LIST_ENDPOINT_GROUPS = {
        "endpoint_groups": [
            {
                "id": 1,
                "name": "SERVICE_GROUP1",
                "description": "FAKE SERVICE ENDPOINT GROUP",
                "links": {
                    "self": "http://example.com/identity/v3/OS-EP-FILTER/" +
                            "endpoint_groups/1"
                },
                "filters": {
                    "service_id": 1
                }
            },
            {
                "id": 2,
                "name": "SERVICE_GROUP2",
                "description": "FAKE SERVICE ENDPOINT GROUP",
                "links": {
                    "self": "http://example.com/identity/v3/OS-EP-FILTER/" +
                            "endpoint_groups/2"
                },
                "filters": {
                    "service_id": 2
                }
            }
        ]
    }

    def setUp(self):
        super(TestEndPointGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = endpoint_groups_client.EndPointGroupsClient(
            fake_auth, 'identity', 'regionOne')

    def _test_create_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_ENDPOINT_GROUP,
            bytes_body,
            status=201,
            name="FAKE_ENDPOINT_GROUP",
            filters={'service_id': "1"})

    def _test_show_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ENDPOINT_GROUP_INFO,
            bytes_body,
            endpoint_group_id="1")

    def _test_check_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.check_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            bytes_body,
            status=200,
            endpoint_group_id="1")

    def _test_update_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_ENDPOINT_GROUP_INFO,
            bytes_body,
            endpoint_group_id="1",
            name="NewName")

    def _test_list_endpoint_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoint_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ENDPOINT_GROUPS,
            bytes_body)

    def test_create_endpoint_group_with_str_body(self):
        self._test_create_endpoint_group()

    def test_create_endpoint_group_with_bytes_body(self):
        self._test_create_endpoint_group(bytes_body=True)

    def test_show_endpoint_group_with_str_body(self):
        self._test_show_endpoint_group()

    def test_show_endpoint_group_with_bytes_body(self):
        self._test_show_endpoint_group(bytes_body=True)

    def test_check_endpoint_group_with_str_body(self):
        self._test_check_endpoint_group()

    def test_check_endpoint_group_with_bytes_body(self):
        self._test_check_endpoint_group(bytes_body=True)

    def test_list_endpoint_groups_with_str_body(self):
        self._test_list_endpoint_groups()

    def test_list_endpoint_groups_with_bytes_body(self):
        self._test_list_endpoint_groups(bytes_body=True)

    def test_update_endpoint_group_with_str_body(self):
        self._test_update_endpoint_group()

    def test_update_endpoint_group_with_bytes_body(self):
        self._test_update_endpoint_group(bytes_body=True)

    def test_delete_endpoint_group(self):
        self.check_service_client_function(
            self.client.delete_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            endpoint_group_id="1",
            status=204)
