# Copyright (C) 2017 Dell Inc. or its subsidiaries.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy

from tempest.lib.services.volume.v3 import group_types_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestGroupTypesClient(base.BaseServiceTest):
    FAKE_CREATE_GROUP_TYPE = {
        "group_type": {
            "name": "group-type-001",
            "description": "Test group type 1",
            "group_specs": {},
            "is_public": True,
        }
    }

    FAKE_INFO_GROUP_TYPE = {
        "group_type": {
            "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
            "name": "group-type-001",
            "description": "Test group type 1",
            "is_public": True,
            "created_at": "20127-06-20T03:50:07Z",
            "group_specs": {},
        }
    }

    FAKE_LIST_GROUP_TYPES = {
        "group_types": [
            {
                "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
                "name": "group-type-001",
                "description": "Test group type 1",
                "is_public": True,
                "created_at": "2017-06-20T03:50:07Z",
                "group_specs": {},
            },
            {
                "id": "e479997c-650b-40a4-9dfe-77655818b0d2",
                "name": "group-type-002",
                "description": "Test group type 2",
                "is_public": True,
                "created_at": "2017-06-19T01:52:47Z",
                "group_specs": {},
            },
            {
                "id": "c5c4769e-213c-40a6-a568-8e797bb691d4",
                "name": "group-type-003",
                "description": "Test group type 3",
                "is_public": True,
                "created_at": "2017-06-18T06:34:32Z",
                "group_specs": {},
            }
        ]
    }

    FAKE_CREATE_GROUP_TYPE_SPECS = {
        "group_specs": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    FAKE_LIST_GROUP_TYPE_SPECS = {
        "group_specs": {
            "key1": "value1",
            "key2": "value2"
        }
    }

    FAKE_SHOW_GROUP_TYPE_SPECS_ITEM = {
        "key1": "value1"
    }

    FAKE_UPDATE_GROUP_TYPE_SPECS_ITEM = {
        "key2": "value2-updated"
    }

    def setUp(self):
        super(TestGroupTypesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = group_types_client.GroupTypesClient(fake_auth,
                                                          'volume',
                                                          'regionOne')

    def _test_create_group_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_type,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_TYPE,
            bytes_body,
            status=202)

    def _test_show_group_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_group_type,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_GROUP_TYPE,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_list_group_types(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_types,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_GROUP_TYPES,
            bytes_body)

    def _test_update_group_types(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_INFO_GROUP_TYPE)
        resp_body['group_type'].pop('created_at')

        self.check_service_client_function(
            self.client.update_group_type,
            'tempest.lib.common.rest_client.RestClient.put',
            resp_body,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            name='updated-group-type-name')

    def _test_create_or_update_group_type_specs(self, bytes_body=False):
        group_specs = self.FAKE_CREATE_GROUP_TYPE_SPECS['group_specs']
        self.check_service_client_function(
            self.client.create_or_update_group_type_specs,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_TYPE_SPECS,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            group_specs=group_specs,
            status=202)

    def _test_list_group_type_specs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_group_type_specs,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_GROUP_TYPE_SPECS,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_show_group_type_specs_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_group_type_specs_item,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_GROUP_TYPE_SPECS_ITEM,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            spec_id="key1")

    def _test_update_group_type_specs_item(self, bytes_body=False):
        spec = self.FAKE_UPDATE_GROUP_TYPE_SPECS_ITEM
        self.check_service_client_function(
            self.client.update_group_type_specs_item,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_GROUP_TYPE_SPECS_ITEM,
            bytes_body,
            group_type_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            spec_id="key2",
            spec=spec)

    def test_create_group_type_with_str_body(self):
        self._test_create_group_type()

    def test_create_group_type_with_bytes_body(self):
        self._test_create_group_type(bytes_body=True)

    def test_delete_group_type(self):
        self.check_service_client_function(
            self.client.delete_group_type,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            group_type_id='0e58433f-d108-4bf3-a22c-34e6b71ef86b',
            status=202)

    def test_show_group_type_with_str_body(self):
        self._test_show_group_type()

    def test_show_group_type_with_bytes_body(self):
        self._test_show_group_type(bytes_body=True)

    def test_list_group_types_with_str_body(self):
        self._test_list_group_types()

    def test_list_group_types_with_bytes_body(self):
        self._test_list_group_types(bytes_body=True)

    def test_update_group_types_with_str_body(self):
        self._test_update_group_types()

    def test_update_group_types_with_bytes_body(self):
        self._test_update_group_types(bytes_body=True)

    def test_create_or_update_group_type_specs_with_str_body(self):
        self._test_create_or_update_group_type_specs()

    def test_create_or_update_group_type_specs_with_bytes_body(self):
        self._test_create_or_update_group_type_specs(bytes_body=True)

    def test_list_group_type_specs_with_str_body(self):
        self._test_list_group_type_specs()

    def test_list_group_type_specs_with_bytes_body(self):
        self._test_list_group_type_specs(bytes_body=True)

    def test_show_group_type_specs_item_with_str_body(self):
        self._test_show_group_type_specs_item()

    def test_show_group_type_specs_item_with_bytes_body(self):
        self._test_show_group_type_specs_item(bytes_body=True)

    def test_update_group_type_specs_item_with_str_body(self):
        self._test_update_group_type_specs_item()

    def test_update_group_type_specs_item_with_bytes_body(self):
        self._test_update_group_type_specs_item(bytes_body=True)

    def test_delete_group_type_specs_item(self):
        self.check_service_client_function(
            self.client.delete_group_type_specs_item,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            group_type_id='0e58433f-d108-4bf3-a22c-34e6b71ef86b',
            spec_id='key1',
            status=202)
