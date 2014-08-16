# Copyright 2012 OpenStack Foundation
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
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class VolumeTypesTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    def _delete_volume(self, volume_id):
        self.volumes_client.delete_volume(volume_id)
        self.volumes_client.wait_for_resource_deletion(volume_id)

    def _delete_volume_type(self, volume_type_id):
        self.client.delete_volume_type(volume_type_id)

    @test.attr(type='smoke')
    def test_volume_type_list(self):
        # List Volume types.
        _, body = self.client.list_volume_types()
        self.assertIsInstance(body, list)

    @test.attr(type='smoke')
    def test_create_get_delete_volume_with_volume_type_and_extra_specs(self):
        # Create/get/delete volume with volume_type and extra spec.
        volume = {}
        vol_name = data_utils.rand_name("volume-")
        vol_type_name = data_utils.rand_name("volume-type-")
        proto = CONF.volume.storage_protocol
        vendor = CONF.volume.vendor_name
        extra_specs = {"storage_protocol": proto,
                       "vendor_name": vendor}
        body = {}
        _, body = self.client.create_volume_type(
            vol_type_name,
            extra_specs=extra_specs)
        self.assertIn('id', body)
        self.addCleanup(self._delete_volume_type, body['id'])
        self.assertIn('name', body)
        _, volume = self.volumes_client.create_volume(
            size=1, display_name=vol_name,
            volume_type=vol_type_name)
        self.assertIn('id', volume)
        self.addCleanup(self._delete_volume, volume['id'])
        self.assertIn('display_name', volume)
        self.assertEqual(volume['display_name'], vol_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertTrue(volume['id'] is not None,
                        "Field volume id is empty or not found.")
        self.volumes_client.wait_for_volume_status(volume['id'],
                                                   'available')
        _, fetched_volume = self.volumes_client.get_volume(volume['id'])
        self.assertEqual(vol_name, fetched_volume['display_name'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(volume['id'], fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(vol_type_name, fetched_volume['volume_type'],
                         'The fetched Volume is different '
                         'from the created Volume')

    @test.attr(type='smoke')
    def test_volume_type_create_get_delete(self):
        # Create/get volume type.
        body = {}
        name = data_utils.rand_name("volume-type-")
        proto = CONF.volume.storage_protocol
        vendor = CONF.volume.vendor_name
        extra_specs = {"storage_protocol": proto,
                       "vendor_name": vendor}
        _, body = self.client.create_volume_type(
            name,
            extra_specs=extra_specs)
        self.assertIn('id', body)
        self.addCleanup(self._delete_volume_type, body['id'])
        self.assertIn('name', body)
        self.assertEqual(body['name'], name,
                         "The created volume_type name is not equal "
                         "to the requested name")
        self.assertTrue(body['id'] is not None,
                        "Field volume_type id is empty or not found.")
        _, fetched_volume_type = self.client.get_volume_type(body['id'])
        self.assertEqual(name, fetched_volume_type['name'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')
        self.assertEqual(str(body['id']), fetched_volume_type['id'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')
        self.assertEqual(extra_specs, fetched_volume_type['extra_specs'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')

    @test.attr(type='smoke')
    def test_volume_type_encryption_create_get_delete(self):
        # Create/get/delete encryption type.
        provider = "LuksEncryptor"
        control_location = "front-end"
        name = data_utils.rand_name("volume-type-")
        _, body = self.client.create_volume_type(name)
        self.addCleanup(self._delete_volume_type, body['id'])

        # Create encryption type
        _, encryption_type = self.client.create_encryption_type(
            body['id'], provider=provider,
            control_location=control_location)
        self.assertIn('volume_type_id', encryption_type)
        self.assertEqual(provider, encryption_type['provider'],
                         "The created encryption_type provider is not equal "
                         "to the requested provider")
        self.assertEqual(control_location, encryption_type['control_location'],
                         "The created encryption_type control_location is not "
                         "equal to the requested control_location")

        # Get encryption type
        _, fetched_encryption_type = self.client.get_encryption_type(
            encryption_type['volume_type_id'])
        self.assertEqual(provider,
                         fetched_encryption_type['provider'],
                         'The fetched encryption_type provider is different '
                         'from the created encryption_type')
        self.assertEqual(control_location,
                         fetched_encryption_type['control_location'],
                         'The fetched encryption_type control_location is '
                         'different from the created encryption_type')

        # Delete encryption type
        self.client.delete_encryption_type(
            encryption_type['volume_type_id'])
        resource = {"id": encryption_type['volume_type_id'],
                    "type": "encryption-type"}
        self.client.wait_for_resource_deletion(resource)
        _, deleted_encryption_type = self.client.get_encryption_type(
            encryption_type['volume_type_id'])
        self.assertEmpty(deleted_encryption_type)
