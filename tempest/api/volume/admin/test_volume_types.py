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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumeTypesTest(base.BaseVolumeAdminTest):

    @decorators.idempotent_id('9d9b28e3-1b2e-4483-a2cc-24aa0ea1de54')
    def test_volume_type_list(self):
        # List volume types.
        body = \
            self.admin_volume_types_client.list_volume_types()['volume_types']
        self.assertIsInstance(body, list)

    @decorators.idempotent_id('c03cc62c-f4e9-4623-91ec-64ce2f9c1260')
    def test_volume_crud_with_volume_type_and_extra_specs(self):
        # Create/update/get/delete volume with volume_type and extra spec.
        volume_types = list()
        vol_name = data_utils.rand_name(self.__class__.__name__ + '-volume')
        proto = CONF.volume.storage_protocol
        vendor = CONF.volume.vendor_name
        extra_specs = {"storage_protocol": proto,
                       "vendor_name": vendor}
        # Create two volume_types
        for _ in range(2):
            vol_type = self.create_volume_type(
                extra_specs=extra_specs)
            volume_types.append(vol_type)
        params = {'name': vol_name,
                  'volume_type': volume_types[0]['id'],
                  'size': CONF.volume.volume_size}

        # Create volume
        volume = self.create_volume(**params)
        self.assertEqual(volume_types[0]['name'], volume["volume_type"])
        self.assertEqual(volume['name'], vol_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertIsNotNone(volume['id'],
                             "Field volume id is empty or not found.")

        # Update volume with new volume_type
        self.volumes_client.retype_volume(volume['id'],
                                          new_type=volume_types[1]['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

        # Get volume details and Verify
        fetched_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(volume_types[1]['name'],
                         fetched_volume['volume_type'],
                         'The fetched Volume type is different '
                         'from updated volume type')
        self.assertEqual(vol_name, fetched_volume['name'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(volume['id'], fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')

    @decorators.idempotent_id('4e955c3b-49db-4515-9590-0c99f8e471ad')
    def test_volume_type_create_get_delete(self):
        # Create/get volume type.
        name = data_utils.rand_name(self.__class__.__name__ + '-volume-type')
        description = data_utils.rand_name("volume-type-description")
        proto = CONF.volume.storage_protocol
        vendor = CONF.volume.vendor_name
        extra_specs = {"storage_protocol": proto,
                       "vendor_name": vendor}
        params = {'name': name,
                  'description': description,
                  'extra_specs': extra_specs,
                  'os-volume-type-access:is_public': True}
        body = self.create_volume_type(**params)
        self.assertIn('name', body)
        self.assertEqual(name, body['name'],
                         "The created volume_type name is not equal "
                         "to the requested name")
        self.assertEqual(description, body['description'],
                         "The created volume_type_description name is "
                         "not equal to the requested name")
        self.assertIsNotNone(body['id'],
                             "Field volume_type id is empty or not found.")
        fetched_volume_type = self.admin_volume_types_client.show_volume_type(
            body['id'])['volume_type']
        self.assertEqual(name, fetched_volume_type['name'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')
        self.assertEqual(str(body['id']), fetched_volume_type['id'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')
        self.assertEqual(extra_specs, fetched_volume_type['extra_specs'],
                         'The fetched Volume_type is different '
                         'from the created Volume_type')
        self.assertEqual(description, fetched_volume_type['description'])
        self.assertEqual(body['is_public'],
                         fetched_volume_type['is_public'])
        self.assertEqual(
            body['os-volume-type-access:is_public'],
            fetched_volume_type['os-volume-type-access:is_public'])

    @decorators.idempotent_id('7830abd0-ff99-4793-a265-405684a54d46')
    def test_volume_type_encryption_create_get_update_delete(self):
        # Create/get/update/delete encryption type.
        create_kwargs = {'provider': 'LuksEncryptor',
                         'control_location': 'front-end'}
        volume_type_id = self.create_volume_type()['id']

        # Create encryption type
        encryption_type = \
            self.admin_encryption_types_client.create_encryption_type(
                volume_type_id, **create_kwargs)['encryption']
        self.assertIn('volume_type_id', encryption_type)
        for key in create_kwargs:
            self.assertEqual(create_kwargs[key], encryption_type[key],
                             'The created encryption_type %s is different '
                             'from the requested encryption_type' % key)

        # Get encryption type
        encrypt_type_id = encryption_type['volume_type_id']
        fetched_encryption_type = (
            self.admin_encryption_types_client.show_encryption_type(
                encrypt_type_id))
        for key in create_kwargs:
            self.assertEqual(create_kwargs[key], fetched_encryption_type[key],
                             'The fetched encryption_type %s is different '
                             'from the created encryption_type' % key)

        # Update encryption type
        update_kwargs = {'key_size': 128,
                         'provider': 'SomeProvider',
                         'cipher': 'aes-xts-plain64',
                         'control_location': 'back-end'}
        self.admin_encryption_types_client.update_encryption_type(
            encrypt_type_id, **update_kwargs)
        updated_encryption_type = (
            self.admin_encryption_types_client.show_encryption_type(
                encrypt_type_id))
        for key in update_kwargs:
            self.assertEqual(update_kwargs[key], updated_encryption_type[key],
                             'The fetched encryption_type %s is different '
                             'from the updated encryption_type' % key)

        # Get encryption specs item
        key = 'cipher'
        item = self.admin_encryption_types_client.show_encryption_specs_item(
            encrypt_type_id, key)
        self.assertEqual(update_kwargs[key], item[key])

        # Delete encryption type
        self.admin_encryption_types_client.delete_encryption_type(
            encrypt_type_id)
        self.admin_encryption_types_client.wait_for_resource_deletion(
            encrypt_type_id)
        deleted_encryption_type = (
            self.admin_encryption_types_client.show_encryption_type(
                encrypt_type_id))
        self.assertEmpty(deleted_encryption_type)

    @decorators.idempotent_id('cf9f07c6-db9e-4462-a243-5933ad65e9c8')
    def test_volume_type_update(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # New volume type details
        name = data_utils.rand_name("volume-type")
        description = data_utils.rand_name("volume-type-description")
        is_public = not volume_type['is_public']

        # Update volume type details
        kwargs = {'name': name,
                  'description': description,
                  'is_public': is_public}
        updated_vol_type = self.admin_volume_types_client.update_volume_type(
            volume_type['id'], **kwargs)['volume_type']

        # Verify volume type details were updated
        self.assertEqual(name, updated_vol_type['name'])
        self.assertEqual(description, updated_vol_type['description'])
        self.assertEqual(is_public, updated_vol_type['is_public'])
