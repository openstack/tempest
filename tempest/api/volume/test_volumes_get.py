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

from tempest_lib.common.utils import data_utils
from testtools import matchers

from tempest.api.volume import base
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesV2GetTest(base.BaseVolumeTest):

    @classmethod
    def setup_clients(cls):
        super(VolumesV2GetTest, cls).setup_clients()
        cls.client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(VolumesV2GetTest, cls).resource_setup()

        cls.name_field = cls.special_fields['name_field']
        cls.descrip_field = cls.special_fields['descrip_field']

    def _delete_volume(self, volume_id):
        self.client.delete_volume(volume_id)
        self.client.wait_for_resource_deletion(volume_id)

    def _volume_create_get_update_delete(self, **kwargs):
        # Create a volume, Get it's details and Delete the volume
        volume = {}
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'Test'}
        # Create a volume
        kwargs[self.name_field] = v_name
        kwargs['metadata'] = metadata
        volume = self.client.create_volume(**kwargs)
        self.assertIn('id', volume)
        self.addCleanup(self._delete_volume, volume['id'])
        self.client.wait_for_volume_status(volume['id'], 'available')
        self.assertIn(self.name_field, volume)
        self.assertEqual(volume[self.name_field], v_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertTrue(volume['id'] is not None,
                        "Field volume id is empty or not found.")
        # Get Volume information
        fetched_volume = self.client.show_volume(volume['id'])
        self.assertEqual(v_name,
                         fetched_volume[self.name_field],
                         'The fetched Volume name is different '
                         'from the created Volume')
        self.assertEqual(volume['id'],
                         fetched_volume['id'],
                         'The fetched Volume id is different '
                         'from the created Volume')
        self.assertThat(fetched_volume['metadata'].items(),
                        matchers.ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')

        if 'imageRef' in kwargs:
            self.assertEqual('true', fetched_volume['bootable'])
        if 'imageRef' not in kwargs:
            self.assertEqual('false', fetched_volume['bootable'])

        # Update Volume
        # Test volume update when display_name is same with original value
        params = {self.name_field: v_name}
        self.client.update_volume(volume['id'], **params)
        # Test volume update when display_name is new
        new_v_name = data_utils.rand_name('new-Volume')
        new_desc = 'This is the new description of volume'
        params = {self.name_field: new_v_name,
                  self.descrip_field: new_desc}
        update_volume = self.client.update_volume(volume['id'], **params)
        # Assert response body for update_volume method
        self.assertEqual(new_v_name, update_volume[self.name_field])
        self.assertEqual(new_desc, update_volume[self.descrip_field])
        # Assert response body for show_volume method
        updated_volume = self.client.show_volume(volume['id'])
        self.assertEqual(volume['id'], updated_volume['id'])
        self.assertEqual(new_v_name, updated_volume[self.name_field])
        self.assertEqual(new_desc, updated_volume[self.descrip_field])
        self.assertThat(updated_volume['metadata'].items(),
                        matchers.ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')
        # Test volume create when display_name is none and display_description
        # contains specific characters,
        # then test volume update if display_name is duplicated
        new_volume = {}
        new_v_desc = data_utils.rand_name('@#$%^* description')
        params = {self.descrip_field: new_v_desc,
                  'availability_zone': volume['availability_zone']}
        new_volume = self.client.create_volume(**params)
        self.assertIn('id', new_volume)
        self.addCleanup(self._delete_volume, new_volume['id'])
        self.client.wait_for_volume_status(new_volume['id'], 'available')

        params = {self.name_field: volume[self.name_field],
                  self.descrip_field: volume[self.descrip_field]}
        self.client.update_volume(new_volume['id'], **params)

        if 'imageRef' in kwargs:
            self.assertEqual('true', updated_volume['bootable'])
        if 'imageRef' not in kwargs:
            self.assertEqual('false', updated_volume['bootable'])

    @test.attr(type='smoke')
    @test.idempotent_id('27fb0e9f-fb64-41dd-8bdb-1ffa762f0d51')
    def test_volume_create_get_update_delete(self):
        self._volume_create_get_update_delete()

    @test.attr(type='smoke')
    @test.idempotent_id('54a01030-c7fc-447c-86ee-c1182beae638')
    @test.services('image')
    def test_volume_create_get_update_delete_from_image(self):
        self._volume_create_get_update_delete(imageRef=CONF.compute.image_ref)

    @test.attr(type='gate')
    @test.idempotent_id('3f591b4a-7dc6-444c-bd51-77469506b3a1')
    def test_volume_create_get_update_delete_as_clone(self):
        origin = self.create_volume()
        self._volume_create_get_update_delete(source_volid=origin['id'])


class VolumesV1GetTest(VolumesV2GetTest):
    _api_version = 1
