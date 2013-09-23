# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.test import services


class VolumesGetTest(base.BaseVolumeTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesGetTest, cls).setUpClass()
        cls.client = cls.volumes_client

    def _delete_volume(self, volume_id):
        resp, _ = self.client.delete_volume(volume_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_resource_deletion(volume_id)

    def _is_true(self, val):
        # NOTE(jdg): Temporary conversion method to get cinder patch
        # merged.  Then we'll make this strict again and
        #specifically check "true" or "false"
        if val in ['true', 'True', True]:
            return True
        else:
            return False

    def _volume_create_get_update_delete(self, **kwargs):
        # Create a volume, Get it's details and Delete the volume
        volume = {}
        v_name = rand_name('Volume')
        metadata = {'Type': 'Test'}
        # Create a volume
        resp, volume = self.client.create_volume(size=1,
                                                 display_name=v_name,
                                                 metadata=metadata,
                                                 **kwargs)
        self.assertEqual(200, resp.status)
        self.assertIn('id', volume)
        self.addCleanup(self._delete_volume, volume['id'])
        self.assertIn('display_name', volume)
        self.assertEqual(volume['display_name'], v_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertTrue(volume['id'] is not None,
                        "Field volume id is empty or not found.")
        self.client.wait_for_volume_status(volume['id'], 'available')
        # Get Volume information
        resp, fetched_volume = self.client.get_volume(volume['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(v_name,
                         fetched_volume['display_name'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(volume['id'],
                         fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(metadata,
                         fetched_volume['metadata'],
                         'The fetched Volume is different '
                         'from the created Volume')

        # NOTE(jdg): Revert back to strict true/false checking
        # after fix for bug #1227837 merges
        boot_flag = self._is_true(fetched_volume['bootable'])
        if 'imageRef' in kwargs:
            self.assertEqual(boot_flag, True)
        if 'imageRef' not in kwargs:
            self.assertEqual(boot_flag, False)

        # Update Volume
        new_v_name = rand_name('new-Volume')
        new_desc = 'This is the new description of volume'
        resp, update_volume = \
            self.client.update_volume(volume['id'],
                                      display_name=new_v_name,
                                      display_description=new_desc)
        # Assert response body for update_volume method
        self.assertEqual(200, resp.status)
        self.assertEqual(new_v_name, update_volume['display_name'])
        self.assertEqual(new_desc, update_volume['display_description'])
        # Assert response body for get_volume method
        resp, updated_volume = self.client.get_volume(volume['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(volume['id'], updated_volume['id'])
        self.assertEqual(new_v_name, updated_volume['display_name'])
        self.assertEqual(new_desc, updated_volume['display_description'])
        self.assertEqual(metadata, updated_volume['metadata'])

        # NOTE(jdg): Revert back to strict true/false checking
        # after fix for bug #1227837 merges
        boot_flag = self._is_true(updated_volume['bootable'])
        if 'imageRef' in kwargs:
            self.assertEqual(boot_flag, True)
        if 'imageRef' not in kwargs:
            self.assertEqual(boot_flag, False)

    @attr(type='gate')
    def test_volume_get_metadata_none(self):
        # Create a volume without passing metadata, get details, and delete
        volume = {}
        v_name = rand_name('Volume-')
        # Create a volume without metadata
        resp, volume = self.client.create_volume(size=1,
                                                 display_name=v_name,
                                                 metadata={})
        self.assertEqual(200, resp.status)
        self.assertIn('id', volume)
        self.addCleanup(self._delete_volume, volume['id'])
        self.assertIn('display_name', volume)
        self.client.wait_for_volume_status(volume['id'], 'available')
        # GET Volume
        resp, fetched_volume = self.client.get_volume(volume['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(fetched_volume['metadata'], {})

    @attr(type='smoke')
    def test_volume_create_get_update_delete(self):
        self._volume_create_get_update_delete()

    @attr(type='smoke')
    @services('image')
    def test_volume_create_get_update_delete_from_image(self):
        self._volume_create_get_update_delete(imageRef=self.
                                              config.compute.image_ref)

    @attr(type='gate')
    def test_volume_create_get_update_delete_as_clone(self):
        origin = self.create_volume(size=1,
                                    display_name="Volume Origin")
        self._volume_create_get_update_delete(source_volid=origin['id'])


class VolumesGetTestXML(VolumesGetTest):
    _interface = "xml"
