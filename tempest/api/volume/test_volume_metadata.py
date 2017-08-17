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
from tempest.lib import decorators


class VolumesMetadataTest(base.BaseVolumeTest):

    @classmethod
    def resource_setup(cls):
        super(VolumesMetadataTest, cls).resource_setup()
        # Create a volume
        cls.volume = cls.create_volume()

    def tearDown(self):
        # Update the metadata to {}
        self.volumes_client.update_volume_metadata(self.volume['id'], {})
        super(VolumesMetadataTest, self).tearDown()

    @decorators.idempotent_id('6f5b125b-f664-44bf-910f-751591fe5769')
    def test_crud_volume_metadata(self):
        # Create metadata for the volume
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3",
                    "key4": "<value&special_chars>"}
        update = {"key4": "value4",
                  "key1": "value1_update"}
        expected = {"key4": "value4"}

        body = self.volumes_client.create_volume_metadata(self.volume['id'],
                                                          metadata)['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(metadata.items()))
        # Get the metadata of the volume
        body = self.volumes_client.show_volume_metadata(
            self.volume['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(metadata.items()),
                        'Create metadata for the volume failed')

        # Update metadata
        body = self.volumes_client.update_volume_metadata(
            self.volume['id'], update)['metadata']
        self.assertEqual(update, body)
        body = self.volumes_client.show_volume_metadata(
            self.volume['id'])['metadata']
        self.assertEqual(update, body, 'Update metadata failed')

        # Delete one item metadata of the volume
        self.volumes_client.delete_volume_metadata_item(
            self.volume['id'], "key1")
        body = self.volumes_client.show_volume_metadata(
            self.volume['id'])['metadata']
        self.assertNotIn("key1", body)
        self.assertThat(body.items(), matchers.ContainsAll(expected.items()),
                        'Delete one item metadata of the volume failed')

    @decorators.idempotent_id('862261c5-8df4-475a-8c21-946e50e36a20')
    def test_update_show_volume_metadata_item(self):
        # Update metadata item for the volume
        metadata = {"key1": "value1",
                    "key2": "value2",
                    "key3": "value3"}
        update_item = {"key3": "value3_update"}
        expect = {"key1": "value1",
                  "key2": "value2",
                  "key3": "value3_update"}
        # Create metadata for the volume
        body = self.volumes_client.create_volume_metadata(
            self.volume['id'], metadata)['metadata']
        self.assertThat(body.items(),
                        matchers.ContainsAll(metadata.items()))
        # Update metadata item
        body = self.volumes_client.update_volume_metadata_item(
            self.volume['id'], "key3", update_item)['meta']
        self.assertEqual(update_item, body)

        # Get a specific metadata item of the volume
        body = self.volumes_client.show_volume_metadata_item(
            self.volume['id'], "key3")['meta']
        self.assertEqual({"key3": expect['key3']}, body)

        # Get the metadata of the volume
        body = self.volumes_client.show_volume_metadata(
            self.volume['id'])['metadata']
        self.assertThat(body.items(), matchers.ContainsAll(expect.items()))
