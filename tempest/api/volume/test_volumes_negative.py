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

import uuid

from tempest.api.volume import base
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class VolumesNegativeTest(base.BaseVolumeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VolumesNegativeTest, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create a test shared instance and volume for attach/detach tests
        vol_name = rand_name('Volume-')

        cls.volume = cls.create_volume(size=1, display_name=vol_name)
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')
        cls.mountpoint = "/dev/vdc"

    @attr(type='gate')
    def test_volume_get_nonexistant_volume_id(self):
        # Should not be able to get a non-existant volume
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          str(uuid.uuid4()))

    @attr(type='gate')
    def test_volume_delete_nonexistant_volume_id(self):
        # Should not be able to delete a non-existant Volume
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          str(uuid.uuid4()))

    @attr(type='gate')
    def test_create_volume_with_invalid_size(self):
        # Should not be able to create volume with invalid size
        # in request
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @attr(type='gate')
    def test_create_volume_with_out_passing_size(self):
        # Should not be able to create volume without passing size
        # in request
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @attr(type='gate')
    def test_create_volume_with_size_zero(self):
        # Should not be able to create volume with size zero
        v_name = rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @attr(type='gate')
    def test_get_invalid_volume_id(self):
        # Should not be able to get volume with invalid id
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          '#$%%&^&^')

    @attr(type='gate')
    def test_get_volume_without_passing_volume_id(self):
        # Should not be able to get volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.get_volume, '')

    @attr(type='gate')
    def test_delete_invalid_volume_id(self):
        # Should not be able to delete volume when invalid ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          '!@#$%^&*()')

    @attr(type='gate')
    def test_delete_volume_without_passing_volume_id(self):
        # Should not be able to delete volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume, '')

    @attr(type=['negative', 'gate'])
    def test_attach_volumes_with_nonexistent_volume_id(self):
        srv_name = rand_name('Instance-')
        resp, server = self.servers_client.create_server(srv_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.addCleanup(self.servers_client.delete_server, server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        self.assertRaises(exceptions.NotFound,
                          self.client.attach_volume,
                          str(uuid.uuid4()),
                          server['id'],
                          self.mountpoint)

    @attr(type=['negative', 'gate'])
    def test_detach_volumes_with_invalid_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.detach_volume,
                          'xxx')


class VolumesNegativeTestXML(VolumesNegativeTest):
    _interface = 'xml'
