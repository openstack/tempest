# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr
from nose.tools import raises

from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.volume.base import BaseVolumeTest


class VolumesNegativeTest(BaseVolumeTest):

    @classmethod
    def setUpClass(cls):
        super(VolumesNegativeTest, cls).setUpClass()
        cls.client = cls.volumes_client

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_volume_get_nonexistant_volume_id(self):
        """Should not be able to get a nonexistant volume"""
        #Creating a nonexistant volume id
        volume_id_list = []
        resp, volumes = self.client.list_volumes()
        for i in range(len(volumes)):
            volume_id_list.append(volumes[i]['id'])
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in volume_id_list:
                break
        #Trying to Get a non existant volume
        resp, volume = self.client.get_volume(non_exist_id)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_volume_delete_nonexistant_volume_id(self):
        """Should not be able to delete a nonexistant Volume"""
        # Creating nonexistant volume id
        volume_id_list = []
        resp, volumes = self.client.list_volumes()
        for i in range(len(volumes)):
            volume_id_list.append(volumes[i]['id'])
        while True:
            non_exist_id = '12345678-abcd-4321-abcd-123456789098'
            if non_exist_id not in volume_id_list:
                break
        # Try to Delete a non existant volume
        resp, body = self.client.delete_volume(non_exist_id)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_volume_with_invalid_size(self):
        """
        Should not be able to create volume with invalid size
        in request
        """
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        resp, volume = self.client.create_volume(size='#$%',
                                                 display_name=v_name,
                                                 metadata=metadata)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_volume_with_out_passing_size(self):
        """
        Should not be able to create volume without passing size
        in request
        """
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        resp, volume = self.client.create_volume(size='',
                                                 display_name=v_name,
                                                 metadata=metadata)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_volume_with_size_zero(self):
        """
        Should not be able to create volume with size zero
        """
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        resp, volume = self.client.create_volume(size='0',
                                                 display_name=v_name,
                                                 metadata=metadata)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_invalid_volume_id(self):
        """
        Should not be able to get volume with invalid id
        """
        resp, volume = self.client.get_volume('#$%%&^&^')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_volume_without_passing_volume_id(self):
        """
        Should not be able to get volume when empty ID is passed
        """
        resp, volume = self.client.get_volume('')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_invalid_volume_id(self):
        """
        Should not be able to delete volume when invalid ID is passed
        """
        resp, volume = self.client.delete_volume('!@#$%^&*()')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_volume_without_passing_volume_id(self):
        """
        Should not be able to delete volume when empty ID is passed
        """
        resp, volume = self.client.delete_volume('')
