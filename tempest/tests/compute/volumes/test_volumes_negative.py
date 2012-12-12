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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute import base


class VolumesNegativeTestBase(object):

    @attr(type='negative')
    def test_volume_get_nonexistant_volume_id(self):
        """Negative: Should not be able to get details of nonexistant volume"""
        #Creating a nonexistant volume id
        volume_id_list = list()
        resp, body = self.client.list_volumes()
        for i in range(len(body)):
            volume_id_list.append(body[i]['id'])
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in volume_id_list:
                break
        #Trying to GET a non existant volume
        try:
            resp, body = self.client.get_volume(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to GET the details from a '
                      'nonexistant volume')

    @attr(type='negative')
    def test_volume_delete_nonexistant_volume_id(self):
        """Negative: Should not be able to delete nonexistant Volume"""
        #Creating nonexistant volume id
        volume_id_list = list()
        resp, body = self.client.list_volumes()
        for i in range(len(body)):
            volume_id_list.append(body[i]['id'])
        while True:
            non_exist_id = rand_name('999')
            if non_exist_id not in volume_id_list:
                break
        #Trying to DELETE a non existant volume
        try:
            resp, body = self.client.delete_volume(non_exist_id)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Should not be able to DELETE a nonexistant volume')

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_volume_with_invalid_size(self):
        """
        Negative: Should not be able to create volume with invalid size
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
        Negative: Should not be able to create volume without passing size
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
        Negative: Should not be able to create volume with size zero
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
        Negative: Should not be able to get volume with invalid id
        """
        resp, volume = self.client.get_volume('#$%%&^&^')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_volume_without_passing_volume_id(self):
        """
        Negative: Should not be able to get volume when empty ID is passed
        """
        resp, volume = self.client.get_volume('')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_invalid_volume_id(self):
        """
        Negative: Should not be able to delete volume when invalid ID is passed
        """
        resp, volume = self.client.delete_volume('!@#$%^&*()')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_volume_without_passing_volume_id(self):
        """
        Negative: Should not be able to delete volume when empty ID is passed
        """
        resp, volume = self.client.delete_volume('')


class VolumesNegativeTestXML(base.BaseComputeTestXML,
                             VolumesNegativeTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(VolumesNegativeTestXML, cls).setUpClass()
        cls.client = cls.volumes_extensions_client


class VolumesNegativeTestJSON(base.BaseComputeTestJSON,
                              VolumesNegativeTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(VolumesNegativeTestJSON, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
