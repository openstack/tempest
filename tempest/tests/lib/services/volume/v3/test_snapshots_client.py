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

from tempest.lib.services.volume.v3 import snapshots_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSnapshotsClient(base.BaseServiceTest):
    FAKE_CREATE_SNAPSHOT = {
        "snapshot": {
            "created_at": "2019-03-11T16:24:34.469003",
            "description": "Daily backup",
            "id": "b36476e5-d18b-47f9-ac69-4818cb43ee21",
            "metadata": {
                "key": "v3"
            },
            "name": "snap-001",
            "size": 10,
            "status": "creating",
            "updated_at": None,
            "volume_id": "d291b81c-6e40-4525-8231-90aa1588121e"
        }
    }

    FAKE_UPDATE_SNAPSHOT_RESPONSE = {
        "snapshot": {
            "created_at": "2019-03-12T04:53:53.426591",
            "description": "This is yet, another snapshot.",
            "id": "4a584cae-e4ce-429b-9154-d4c9eb8fda4c",
            "metadata": {
                "key": "v3"
            },
            "name": "snap-002",
            "size": 10,
            "status": "creating",
            "updated_at": None,
            "volume_id": "070c942d-9909-42e9-a467-7a781f150c58"
        }
    }

    FAKE_INFO_SNAPSHOT = {
        "snapshot": {
            "created_at": "2019-03-12T04:42:00.809352",
            "description": "Daily backup",
            "id": "4a584cae-e4ce-429b-9154-d4c9eb8fda4c",
            "metadata": {
                "key": "v3"
            },
            "name": "snap-001",
            "os-extended-snapshot-attributes:progress": "0%",
            "os-extended-snapshot-attributes:project_id":
                "89afd400-b646-4bbc-b12b-c0a4d63e5bd3",
            "size": 10,
            "status": "creating",
            "updated_at": None,
            "volume_id": "b72c48f1-64b7-4cd8-9745-b12e0be82d37"
        }
    }

    FAKE_LIST_SNAPSHOTS = {
        "snapshots": [
            {
                "created_at": "2019-03-11T16:24:36.464445",
                "description": "Daily backup",
                "id": "d0083dc5-8795-4c1a-bc9c-74f70006c205",
                "metadata": {
                    "key": "v3"
                },
                "name": "snap-001",
                "os-extended-snapshot-attributes:progress": "0%",
                "os-extended-snapshot-attributes:project_id":
                    "89afd400-b646-4bbc-b12b-c0a4d63e5bd3",
                "size": 10,
                "status": "creating",
                "updated_at": None,
                "volume_id": "7acd675e-4e06-4653-af9f-2ecd546342d6"
            }
        ]
    }

    FAKE_SNAPSHOT_METADATA_ITEM = {
        "metadata": {
            "key": "value"
        }
    }

    FAKE_SNAPSHOT_KEY = {
        "meta": {
            "key": "new_value"
        }
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
            bytes_body,
            status=202)

    def _test_show_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_SNAPSHOT,
            bytes_body,
            snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c")

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
            self.FAKE_SNAPSHOT_METADATA_ITEM,
            bytes_body,
            snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c",
            metadata={"key": "value"})

    def _test_update_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_SNAPSHOT_RESPONSE,
            bytes_body,
            snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c")

    def _test_show_snapshot_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot_metadata,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SNAPSHOT_METADATA_ITEM,
            bytes_body,
            snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c")

    def _test_update_snapshot_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot_metadata,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_SNAPSHOT_METADATA_ITEM,
            bytes_body, snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c")

    def _test_update_snapshot_metadata_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_snapshot_metadata_item,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_SNAPSHOT_KEY,
            bytes_body, volume_type_id="cbc36478b0bd8e67e89")

    def _test_show_snapshot_metadata_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot_metadata_item,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SNAPSHOT_KEY,
            bytes_body,
            snapshot_id="4a584cae-e4ce-429b-9154-d4c9eb8fda4c",
            id="key1")

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

    def test_show_snapshot_metadata_item_with_str_body(self):
        self._test_show_snapshot_metadata_item()

    def test_show_snapshot_metadata_item_with_bytes_body(self):
        self._test_show_snapshot_metadata_item(bytes_body=True)

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
