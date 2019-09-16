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

from tempest.lib.services.volume.v3 import group_snapshots_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestGroupSnapshotsClient(base.BaseServiceTest):
    FAKE_CREATE_GROUP_SNAPSHOT = {
        "group_snapshot": {
            "id": "6f519a48-3183-46cf-a32f-41815f816666",
            "name": "first_group_snapshot",
            "group_type_id": "58737af7-786b-48b7-ab7c-2447e74b0ef4"
        }
    }

    FAKE_INFO_GROUP_SNAPSHOT = {
        "group_snapshot": {
            "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
            "group_id": "49c8c114-0d68-4e89-b8bc-3f5a674d54be",
            "name": "group-snapshot-001",
            "description": "Test group snapshot 1",
            "group_type_id": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
            "status": "available",
            "created_at": "2017-06-20T03:50:07Z"
        }
    }

    FAKE_LIST_GROUP_SNAPSHOTS = {
        "group_snapshots": [
            {
                "id": "0e701ab8-1bec-4b9f-b026-a7ba4af13578",
                "group_id": "49c8c114-0d68-4e89-b8bc-3f5a674d54be",
                "name": "group-snapshot-001",
                "description": "Test group snapshot 1",
                "group_type_id": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "status": "available",
                "created_at": "2017-06-20T03:50:07Z",
            },
            {
                "id": "e479997c-650b-40a4-9dfe-77655818b0d2",
                "group_id": "49c8c114-0d68-4e89-b8bc-3f5a674d54be",
                "name": "group-snapshot-002",
                "description": "Test group snapshot 2",
                "group_type_id": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "status": "available",
                "created_at": "2017-06-19T01:52:47Z",
            },
            {
                "id": "c5c4769e-213c-40a6-a568-8e797bb691d4",
                "group_id": "49c8c114-0d68-4e89-b8bc-3f5a674d54be",
                "name": "group-snapshot-003",
                "description": "Test group snapshot 3",
                "group_type_id": "0e58433f-d108-4bf3-a22c-34e6b71ef86b",
                "status": "available",
                "created_at": "2017-06-18T06:34:32Z",
            }
        ]
    }

    def setUp(self):
        super(TestGroupSnapshotsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = group_snapshots_client.GroupSnapshotsClient(
            fake_auth, 'volume', 'regionOne')

    def _test_create_group_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_snapshot,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_SNAPSHOT,
            bytes_body,
            group_id="49c8c114-0d68-4e89-b8bc-3f5a674d54be",
            status=202)

    def _test_show_group_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_group_snapshot,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_GROUP_SNAPSHOT,
            bytes_body,
            group_snapshot_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_list_group_snapshots(self, detail=False, bytes_body=False,
                                   mock_args='group_snapshots', **params):
        resp_body = []
        if detail:
            resp_body = self.FAKE_LIST_GROUP_SNAPSHOTS
        else:
            resp_body = {
                'group_snapshots': [{
                    'id': group_snapshot['id'],
                    'name': group_snapshot['name']}
                    for group_snapshot in
                    self.FAKE_LIST_GROUP_SNAPSHOTS['group_snapshots']
                ]
            }
        self.check_service_client_function(
            self.client.list_group_snapshots,
            'tempest.lib.common.rest_client.RestClient.get',
            resp_body,
            to_utf=bytes_body,
            mock_args=[mock_args],
            detail=detail,
            **params)

    def test_create_group_snapshot_with_str_body(self):
        self._test_create_group_snapshot()

    def test_create_group_snapshot_with_bytes_body(self):
        self._test_create_group_snapshot(bytes_body=True)

    def test_show_group_snapshot_with_str_body(self):
        self._test_show_group_snapshot()

    def test_show_group_snapshot_with_bytes_body(self):
        self._test_show_group_snapshot(bytes_body=True)

    def test_list_group_snapshots_with_str_body(self):
        self._test_list_group_snapshots()

    def test_list_group_snapshots_with_bytes_body(self):
        self._test_list_group_snapshots(bytes_body=True)

    def test_list_group_snapshots_with_detail_with_str_body(self):
        mock_args = "group_snapshots/detail"
        self._test_list_group_snapshots(detail=True, mock_args=mock_args)

    def test_list_group_snapshots_with_detail_with_bytes_body(self):
        mock_args = "group_snapshots/detail"
        self._test_list_group_snapshots(detail=True, bytes_body=True,
                                        mock_args=mock_args)

    def test_list_group_snapshots_with_params(self):
        # Run the test separately for each param, to avoid assertion error
        # resulting from randomized params order.
        mock_args = 'group_snapshots?sort_key=name'
        self._test_list_group_snapshots(mock_args=mock_args, sort_key='name')

        mock_args = 'group_snapshots/detail?limit=10'
        self._test_list_group_snapshots(detail=True, bytes_body=True,
                                        mock_args=mock_args, limit=10)

    def test_delete_group_snapshot(self):
        self.check_service_client_function(
            self.client.delete_group_snapshot,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            group_snapshot_id='0e701ab8-1bec-4b9f-b026-a7ba4af13578',
            status=202)

    def test_reset_group_snapshot_status(self):
        self.check_service_client_function(
            self.client.reset_group_snapshot_status,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            status=202,
            group_snapshot_id='0e701ab8-1bec-4b9f-b026-a7ba4af13578',
            status_to_set='error')
