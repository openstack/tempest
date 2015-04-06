# Copyright 2013 Huawei Technologies Co.,LTD
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

from tempest.api.volume import base
from tempest import test


class SnapshotV2MetadataTestJSON(base.BaseVolumeTest):

    @classmethod
    def setup_clients(cls):
        super(SnapshotV2MetadataTestJSON, cls).setup_clients()
        cls.client = cls.snapshots_client

    @classmethod
    def resource_setup(cls):
        super(SnapshotV2MetadataTestJSON, cls).resource_setup()
        # Create a volume
        cls.volume = cls.create_volume()
        # Create a snapshot
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])
        cls.snapshot_id = cls.snapshot['id']

    def tearDown(self):
        # Update the metadata to {}
        self.client.update_snapshot_metadata(self.snapshot_id, {})
        super(SnapshotV2MetadataTestJSON, self).tearDown()

    @test.attr(type='gate')
    @test.idempotent_id('a2f20f99-e363-4584-be97-bc33afb1a56c')
    def test_create_get_delete_snapshot_metadata(self):
        # Create metadata for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        expected = {"key2": "value2",
                    "key3": "value3"}
        body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                    metadata)
        # Get the metadata of the snapshot
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(metadata, body)
        # Delete one item metadata of the snapshot
        self.client.delete_snapshot_metadata_item(
            self.snapshot_id, "key1")
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(expected, body)

    @test.attr(type='gate')
    @test.idempotent_id('bd2363bc-de92-48a4-bc98-28943c6e4be1')
    def test_update_snapshot_metadata(self):
        # Update metadata for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update = {"key3": "value3_update",
                  "key4": "value4"}
        # Create metadata for the snapshot
        body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                    metadata)
        # Get the metadata of the snapshot
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(metadata, body)
        # Update metadata item
        body = self.client.update_snapshot_metadata(
            self.snapshot_id, update)
        # Get the metadata of the snapshot
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(update, body)

    @test.attr(type='gate')
    @test.idempotent_id('e8ff85c5-8f97-477f-806a-3ac364a949ed')
    def test_update_snapshot_metadata_item(self):
        # Update metadata item for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update_item = {"key3": "value3_update"}
        expect = {"key1": "value1",
                  "key2": "value2",
                  "key3": "value3_update"}
        # Create metadata for the snapshot
        body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                    metadata)
        # Get the metadata of the snapshot
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(metadata, body)
        # Update metadata item
        body = self.client.update_snapshot_metadata_item(
            self.snapshot_id, "key3", update_item)
        # Get the metadata of the snapshot
        body = self.client.show_snapshot_metadata(self.snapshot_id)
        self.assertEqual(expect, body)


class SnapshotV1MetadataTestJSON(SnapshotV2MetadataTestJSON):
    _api_version = 1
