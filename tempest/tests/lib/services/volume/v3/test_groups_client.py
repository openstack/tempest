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

from tempest.lib.services.volume.v3 import groups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestGroupsClient(base.BaseServiceTest):
    FAKE_CREATE_GROUP = {
        "group": {
            "id": "6f519a48-3183-46cf-a32f-41815f816666",
            "name": "first_group"
        }
    }

    FAKE_CREATE_GROUP_FROM_GROUP_SNAPSHOT = {
        "group": {
            "id": "6f519a48-3183-46cf-a32f-41815f816668",
            "name": "first_group"
        }
    }

    FAKE_CREATE_GROUP_FROM_GROUP = {
        "group": {
            "id": "6f519a48-3183-46cf-a32f-41815f816667",
            "name": "other_group"
        }
    }

    FAKE_UPDATE_GROUP = {
        "group": {
            "name": "new-group",
            "description": "New test group",
            "add_volumes": "27d45037-ade3-4a87-b729-dba3293c06f3,"
                           "6e7cd916-d961-41cc-b3bd-0601ca0c701f",
            "remove_volumes": "4d580519-6467-448e-95e9-5b25c94d83c7,"
                              "ea22464c-f095-4a87-a31f-c5d34e0c6fc9"
        }
    }

    FAKE_INFO_GROUP = {
        "group": {
            "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
            "name": "group-001",
            "description": "Test group 1",
            "group_type": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
            "volume_types": ["2103099d-7cc3-4e52-a2f1-23a5284416f3"],
            "status": "available",
            "availability_zone": "az1",
            "created_at": "20127-06-20T03:50:07Z"
        }
    }

    FAKE_LIST_GROUPS = {
        "groups": [
            {
                "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
                "name": "group-001",
                "description": "Test group 1",
                "group_type": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "volume_types": ["2103099d-7cc3-4e52-a2f1-23a5284416f3"],
                "status": "available",
                "availability_zone": "az1",
                "created_at": "2017-06-20T03:50:07Z",
            },
            {
                "id": "e479997c-650b-40a4-9dfe-77655818b0d2",
                "name": "group-002",
                "description": "Test group 2",
                "group_snapshot_id": "79c9afdb-7e46-4d71-9249-1f022886963c",
                "group_type": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "volume_types": ["2103099d-7cc3-4e52-a2f1-23a5284416f3"],
                "status": "available",
                "availability_zone": "az1",
                "created_at": "2017-06-19T01:52:47Z",
            },
            {
                "id": "c5c4769e-213c-40a6-a568-8e797bb691d4",
                "name": "group-003",
                "description": "Test group 3",
                "source_group_id": "e92f9dc7-0b20-492d-8ab2-3ad8fdac270e",
                "group_type": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "volume_types": ["2103099d-7cc3-4e52-a2f1-23a5284416f3"],
                "status": "available",
                "availability_zone": "az1",
                "created_at": "2017-06-18T06:34:32Z",
            }
        ]
    }

    def setUp(self):
        super(TestGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = groups_client.GroupsClient(fake_auth,
                                                 'volume',
                                                 'regionOne')

    def _test_create_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP,
            bytes_body,
            status=202)

    def _test_show_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_GROUP,
            bytes_body,
            group_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_list_groups(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_GROUPS,
            bytes_body,
            detail=True)

    def test_create_group_with_str_body(self):
        self._test_create_group()

    def test_create_group_with_bytes_body(self):
        self._test_create_group(bytes_body=True)

    def test_show_group_with_str_body(self):
        self._test_show_group()

    def test_show_group_with_bytes_body(self):
        self._test_show_group(bytes_body=True)

    def test_list_groups_with_str_body(self):
        self._test_list_groups()

    def test_list_groups_with_bytes_body(self):
        self._test_list_groups(bytes_body=True)

    def test_delete_group(self):
        self.check_service_client_function(
            self.client.delete_group,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            group_id='0e701ab8-1bec-4b9f-b026-a7ba4af13578',
            status=202)

    def test_create_group_from_group_snapshot(self):
        self.check_service_client_function(
            self.client.create_group_from_source,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_FROM_GROUP_SNAPSHOT,
            status=202)

    def test_create_group_from_group(self):
        self.check_service_client_function(
            self.client.create_group_from_source,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_FROM_GROUP,
            status=202)

    def test_update_group(self):
        self.check_service_client_function(
            self.client.update_group,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            group_id='0e701ab8-1bec-4b9f-b026-a7ba4af13578',
            status=202,
            **self.FAKE_UPDATE_GROUP['group'])

    def test_reset_group_status(self):
        self.check_service_client_function(
            self.client.reset_group_status,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            status=202,
            group_id='0e701ab8-1bec-4b9f-b026-a7ba4af13578',
            status_to_set='error')
