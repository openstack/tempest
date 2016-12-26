# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.volume.v1 import snapshots_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSnapshotsClient(base.BaseServiceTest):
    FAKE_CREATE_SNAPSHOT = {
        "snapshot": {
            "display_name": "snap-001",
            "display_description": "Daily backup",
            "volume_id": "521752a6-acf6-4b2d-bc7a-119f9148cd8c",
            "force": True
        }
    }

    FAKE_UPDATE_SNAPSHOT_REQUEST = {
        "metadata": {
            "key": "v1"
        }
    }

    FAKE_INFO_SNAPSHOT = {
        "snapshot": {
            "id": "3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            "display_name": "snap-001",
            "display_description": "Daily backup",
            "volume_id": "521752a6-acf6-4b2d-bc7a-119f9148cd8c",
            "status": "available",
            "size": 30,
            "created_at": "2012-02-29T03:50:07Z"
        }
    }

    FAKE_LIST_SNAPSHOTS = {
        "snapshots": [
            {
                "id": "3fbbcccf-d058-4502-8844-6feeffdf4cb5",
                "display_name": "snap-001",
                "display_description": "Daily backup",
                "volume_id": "521752a6-acf6-4b2d-bc7a-119f9148cd8c",
                "status": "available",
                "size": 30,
                "created_at": "2012-02-29T03:50:07Z",
                "metadata": {
                    "contents": "junk"
                }
            },
            {
                "id": "e479997c-650b-40a4-9dfe-77655818b0d2",
                "display_name": "snap-002",
                "display_description": "Weekly backup",
                "volume_id": "76b8950a-8594-4e5b-8dce-0dfa9c696358",
                "status": "available",
                "size": 25,
                "created_at": "2012-03-19T01:52:47Z",
                "metadata": {}
            }
        ]
    }

    def setUp(self):
        super(TestSnapshotsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = snapshots_client.SnapshotsClient(fake_auth,
                                                       'volume',
                                                       'regionOne')

    def _test_create_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_snapshot,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SNAPSHOT,
            bytes_body)

    def _test_show_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_SNAPSHOT,
            bytes_body,
            snapshot_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_list_snapshots(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_snapshots,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_SNAPSHOTS,
            bytes_body,
            detail=True)

    def _test_create_snapshot_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_snapshot_metadata,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_INFO_SNAPSHOT,
            bytes_body,
            snapshot_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5",
            metadata={"key": "v1"})

    def _test_update_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_SNAPSHOT_REQUEST,
            bytes_body,
            snapshot_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_show_snapshot_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot_metadata,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_UPDATE_SNAPSHOT_REQUEST,
            bytes_body,
            snapshot_id="3fbbcccf-d058-4502-8844-6feeffdf4cb5")

    def _test_update_snapshot_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot_metadata,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_SNAPSHOT_REQUEST,
            bytes_body, snapshot_id="cbc36478b0bd8e67e89")

    def _test_update_snapshot_metadata_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot_metadata_item,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_INFO_SNAPSHOT,
            bytes_body, volume_type_id="cbc36478b0bd8e67e89")

    def test_create_snapshot_with_str_body(self):
        self._test_create_snapshot()

    def test_create_snapshot_with_bytes_body(self):
        self._test_create_snapshot(bytes_body=True)

    def test_show_snapshot_with_str_body(self):
        self._test_show_snapshot()

    def test_show_snapshot_with_bytes_body(self):
        self._test_show_snapshot(bytes_body=True)

    def test_list_snapshots_with_str_body(self):
        self._test_list_snapshots()

    def test_list_snapshots_with_bytes_body(self):
        self._test_list_snapshots(bytes_body=True)

    def test_create_snapshot_metadata_with_str_body(self):
        self._test_create_snapshot_metadata()

    def test_create_snapshot_metadata_with_bytes_body(self):
        self._test_create_snapshot_metadata(bytes_body=True)

    def test_update_snapshot_with_str_body(self):
        self._test_update_snapshot()

    def test_update_snapshot_with_bytes_body(self):
        self._test_update_snapshot(bytes_body=True)

    def test_show_snapshot_metadata_with_str_body(self):
        self._test_show_snapshot_metadata()

    def test_show_snapshot_metadata_with_bytes_body(self):
        self._test_show_snapshot_metadata(bytes_body=True)

    def test_update_snapshot_metadata_with_str_body(self):
        self._test_update_snapshot_metadata()

    def test_update_snapshot_metadata_with_bytes_body(self):
        self._test_update_snapshot_metadata(bytes_body=True)

    def test_force_delete_snapshot(self):
        self.check_service_client_function(
            self.client.force_delete_snapshot,
            'tempest.lib.common.rest_client.RestClient.post',
            {},
            snapshot_id="521752a6-acf6-4b2d-bc7a-119f9148cd8c",
            status=202)

    def test_delete_snapshot(self):
        self.check_service_client_function(
            self.client.delete_snapshot,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            snapshot_id="521752a6-acf6-4b2d-bc7a-119f9148cd8c",
            status=202)
