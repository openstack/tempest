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

from testtools import matchers

from tempest.api.volume import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class SnapshotMetadataTestJSON(base.BaseVolumeTest):
    """Test snapshot metadata"""

    @classmethod
    def skip_checks(cls):
        super(SnapshotMetadataTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder snapshot feature disabled")

    @classmethod
    def resource_setup(cls):
        super(SnapshotMetadataTestJSON, cls).resource_setup()
        # Create a volume
        cls.volume = cls.create_volume()
        # Create a snapshot
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])

    def tearDown(self):
        # Update the metadata to {}
        self.snapshots_client.update_snapshot_metadata(
            self.snapshot['id'], metadata={})
        super(SnapshotMetadataTestJSON, self).tearDown()

    @decorators.idempotent_id('a2f20f99-e363-4584-be97-bc33afb1a56c')
    def test_crud_snapshot_metadata(self):
        """Test create/get/update/delete snapshot metadata"""
        # Create metadata for the snapshot
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update = {"key3": "value3_update",
                  "key4": "value4"}
        expect = {"key4": "value4"}
        # Create metadata
        body = self.snapshots_client.create_snapshot_metadata(
            self.snapshot['id'], metadata)['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(metadata.items()))

        # Get the metadata of the snapshot
        body = self.snapshots_client.show_snapshot_metadata(
            self.snapshot['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(metadata.items()),
                        'Create snapshot metadata failed')

        # Update metadata
        body = self.snapshots_client.update_snapshot_metadata(
            self.snapshot['id'], metadata=update)['metadata']
        self.assertEqual(update, body)
        body = self.snapshots_client.show_snapshot_metadata(
            self.snapshot['id'])['metadata']
        self.assertEqual(update, body, 'Update snapshot metadata failed')

        # Delete one item metadata of the snapshot
        self.snapshots_client.delete_snapshot_metadata_item(
            self.snapshot['id'], "key3")
        body = self.snapshots_client.show_snapshot_metadata(
            self.snapshot['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(expect.items()),
                        'Delete one item metadata of the snapshot failed')
        self.assertNotIn("key3", body)

    @decorators.idempotent_id('e8ff85c5-8f97-477f-806a-3ac364a949ed')
    def test_update_show_snapshot_metadata_item(self):
        """Test update/show snapshot metadata item"""
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update_item = {"key3": "value3_update"}
        expect = {"key1": "value1",
                  "key2": "value2",
                  "key3": "value3_update"}
        # Create metadata for the snapshot
        self.snapshots_client.create_snapshot_metadata(
            self.snapshot['id'], metadata)
        # Get the metadata of the snapshot
        body = self.snapshots_client.show_snapshot_metadata(
            self.snapshot['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(metadata.items()))
        # Update metadata item
        body = self.snapshots_client.update_snapshot_metadata_item(
            self.snapshot['id'], "key3", meta=update_item)['meta']
        self.assertEqual(update_item, body)

        # Get a specific metadata item of the snapshot
        body = self.snapshots_client.show_snapshot_metadata_item(
            self.snapshot['id'], "key3")['meta']
        self.assertEqual({"key3": expect['key3']}, body)

        # Get the metadata of the snapshot
        body = self.snapshots_client.show_snapshot_metadata(
            self.snapshot['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(expect.items()))
