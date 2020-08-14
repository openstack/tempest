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

import testtools
from testtools import matchers

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class VolumesGetTest(base.BaseVolumeTest):
    """Test getting volume info"""

    def _volume_create_get_update_delete(self, **kwargs):
        # Create a volume, Get it's details and Delete the volume
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        metadata = {'Type': 'Test'}
        # Create a volume
        kwargs['name'] = v_name
        kwargs['metadata'] = metadata
        volume = self.volumes_client.create_volume(**kwargs)['volume']
        self.addCleanup(self.delete_volume, self.volumes_client, volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.assertEqual(volume['name'], v_name,
                         "The created volume name is not equal "
                         "to the requested name")

        # Get Volume information
        fetched_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(v_name,
                         fetched_volume['name'],
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
        else:
            self.assertEqual('false', fetched_volume['bootable'])

        # Update Volume
        # Test volume update when display_name is same with original value
        params = {'name': v_name}
        self.volumes_client.update_volume(volume['id'], **params)
        # Test volume update when display_name is new
        new_v_name = data_utils.rand_name(
            self.__class__.__name__ + '-new-Volume')
        new_desc = 'This is the new description of volume'
        params = {'name': new_v_name,
                  'description': new_desc}
        update_volume = self.volumes_client.update_volume(
            volume['id'], **params)['volume']
        # Assert response body for update_volume method
        self.assertEqual(new_v_name, update_volume['name'])
        self.assertEqual(new_desc, update_volume['description'])
        # Assert response body for show_volume method
        updated_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(volume['id'], updated_volume['id'])
        self.assertEqual(new_v_name, updated_volume['name'])
        self.assertEqual(new_desc, updated_volume['description'])
        self.assertThat(updated_volume['metadata'].items(),
                        matchers.ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')

        # Test volume create when display_name is none and display_description
        # contains specific characters,
        # then test volume update if display_name is duplicated
        new_v_desc = data_utils.rand_name('@#$%^* description')
        params = {'description': new_v_desc,
                  'availability_zone': volume['availability_zone'],
                  'size': CONF.volume.volume_size}
        new_volume = self.volumes_client.create_volume(**params)['volume']
        self.addCleanup(self.delete_volume, self.volumes_client,
                        new_volume['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                new_volume['id'], 'available')

        params = {'name': volume['name'],
                  'description': volume['description']}
        self.volumes_client.update_volume(new_volume['id'], **params)

        if 'imageRef' in kwargs:
            self.assertEqual('true', updated_volume['bootable'])
        else:
            self.assertEqual('false', updated_volume['bootable'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('27fb0e9f-fb64-41dd-8bdb-1ffa762f0d51')
    def test_volume_create_get_update_delete(self):
        """Test Create/Get/Update/Delete of a blank volume"""
        self._volume_create_get_update_delete(size=CONF.volume.volume_size)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('54a01030-c7fc-447c-86ee-c1182beae638')
    @utils.services('image')
    def test_volume_create_get_update_delete_from_image(self):
        """Test Create/Get/Update/Delete of a volume created from image"""
        image = self.images_client.show_image(CONF.compute.image_ref)
        min_disk = image['min_disk']
        disk_size = max(min_disk, CONF.volume.volume_size)
        self._volume_create_get_update_delete(
            imageRef=CONF.compute.image_ref, size=disk_size)

    @decorators.idempotent_id('3f591b4a-7dc6-444c-bd51-77469506b3a1')
    @testtools.skipUnless(CONF.volume_feature_enabled.clone,
                          'Cinder volume clones are disabled')
    def test_volume_create_get_update_delete_as_clone(self):
        """Test Create/Get/Update/Delete of a cloned volume"""
        origin = self.create_volume()
        self._volume_create_get_update_delete(source_volid=origin['id'],
                                              size=CONF.volume.volume_size)


class VolumesSummaryTest(base.BaseVolumeTest):
    """Test volume summary"""

    _api_version = 3
    min_microversion = '3.12'
    max_microversion = 'latest'

    @decorators.idempotent_id('c4f2431e-4920-4736-9e00-4040386b6feb')
    def test_show_volume_summary(self):
        """Test showing volume summary"""
        # check response schema
        self.volumes_client.show_volume_summary()
