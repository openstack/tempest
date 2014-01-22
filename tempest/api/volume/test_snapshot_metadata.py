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


class SnapshotMetadataTest(base.BaseVolumeV1Test):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(SnapshotMetadataTest, cls).setUpClass()
        cls.client = cls.snapshots_client
        # Create a volume
        cls.volume = cls.create_volume()
        # Create a snapshot
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])
        cls.snapshot_id = cls.snapshot['id']

    def tearDown(self):
        # Update the metadata to {}
        self.client.update_snapshot_metadata(self.snapshot_id, {})
        super(SnapshotMetadataTest, self).tearDown()

    @test.attr(type='gate')
    def test_create_get_delete_snapshot_metadata(self):
        # Create metadata for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        expected = {"key2": "value2",
                    "key3": "value3"}
        resp, body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                          metadata)
        self.assertEqual(200, resp.status)
        # Get the metadata of the snapshot
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(metadata, body)
        # Delete one item metadata of the snapshot
        resp, body = self.client.delete_snapshot_metadata_item(
            self.snapshot_id,
            "key1")
        self.assertEqual(200, resp.status)
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(expected, body)

    @test.attr(type='gate')
    def test_update_snapshot_metadata(self):
        # Update metadata for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update = {"key3": "value3_update",
                  "key4": "value4"}
        # Create metadata for the snapshot
        resp, body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                          metadata)
        self.assertEqual(200, resp.status)
        # Get the metadata of the snapshot
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(metadata, body)
        # Update metadata item
        resp, body = self.client.update_snapshot_metadata(
            self.snapshot_id,
            update)
        self.assertEqual(200, resp.status)
        # Get the metadata of the snapshot
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(update, body)

    @test.attr(type='gate')
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
        resp, body = self.client.create_snapshot_metadata(self.snapshot_id,
                                                          metadata)
        self.assertEqual(200, resp.status)
        # Get the metadata of the snapshot
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(metadata, body)
        # Update metadata item
        resp, body = self.client.update_snapshot_metadata_item(
            self.snapshot_id,
            "key3",
            update_item)
        self.assertEqual(200, resp.status)
        # Get the metadata of the snapshot
        resp, body = self.client.get_snapshot_metadata(self.snapshot_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(expect, body)


class SnapshotMetadataTestXML(SnapshotMetadataTest):
    _interface = "xml"
