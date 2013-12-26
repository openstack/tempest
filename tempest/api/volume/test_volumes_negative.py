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

import uuid

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class VolumesNegativeTest(base.BaseVolumeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VolumesNegativeTest, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create a test shared instance and volume for attach/detach tests
        cls.volume = cls.create_volume()
        cls.mountpoint = "/dev/vdc"

    @attr(type=['negative', 'gate'])
    def test_volume_get_nonexistant_volume_id(self):
        # Should not be able to get a non-existant volume
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_volume_delete_nonexistant_volume_id(self):
        # Should not be able to delete a non-existant Volume
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_invalid_size(self):
        # Should not be able to create volume with invalid size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_out_passing_size(self):
        # Should not be able to create volume without passing size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_size_zero(self):
        # Should not be able to create volume with size zero
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_size_negative(self):
        # Should not be able to create volume with size negative
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='-1', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistant_volume_type(self):
        # Should not be able to create volume with non-existant volume type
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', volume_type=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistant_snapshot_id(self):
        # Should not be able to create volume with non-existant snapshot
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', snapshot_id=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistant_source_volid(self):
        # Should not be able to create volume with non-existant source volume
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', source_volid=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_update_volume_with_nonexistant_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id=str(uuid.uuid4()), display_name=v_name,
                          metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_update_volume_with_invalid_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id='#$%%&^&^', display_name=v_name,
                          metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_update_volume_with_empty_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id='', display_name=v_name,
                          metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_get_invalid_volume_id(self):
        # Should not be able to get volume with invalid id
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          '#$%%&^&^')

    @attr(type=['negative', 'gate'])
    def test_get_volume_without_passing_volume_id(self):
        # Should not be able to get volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.get_volume, '')

    @attr(type=['negative', 'gate'])
    def test_delete_invalid_volume_id(self):
        # Should not be able to delete volume when invalid ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          '!@#$%^&*()')

    @attr(type=['negative', 'gate'])
    def test_delete_volume_without_passing_volume_id(self):
        # Should not be able to delete volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume, '')

    @attr(type=['negative', 'gate'])
    def test_attach_volumes_with_nonexistent_volume_id(self):
        srv_name = data_utils.rand_name('Instance-')
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

    @attr(type=['negative', 'gate'])
    def test_volume_extend_with_size_smaller_than_original_size(self):
        # Extend volume with smaller size than original size.
        extend_size = 0
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @attr(type=['negative', 'gate'])
    def test_volume_extend_with_non_number_size(self):
        # Extend volume when size is non number.
        extend_size = 'abc'
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @attr(type=['negative', 'gate'])
    def test_volume_extend_with_None_size(self):
        # Extend volume with None size.
        extend_size = None
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @attr(type=['negative', 'gate'])
    def test_volume_extend_with_nonexistent_volume_id(self):
        # Extend volume size when volume is nonexistent.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(exceptions.NotFound, self.client.extend_volume,
                          str(uuid.uuid4()), extend_size)

    @attr(type=['negative', 'gate'])
    def test_volume_extend_without_passing_volume_id(self):
        # Extend volume size when passing volume id is None.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(exceptions.NotFound, self.client.extend_volume,
                          None, extend_size)

    @attr(type=['negative', 'gate'])
    def test_reserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.reserve_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_unreserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.unreserve_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_reserve_volume_with_negative_volume_status(self):
        # Mark volume as reserved.
        resp, body = self.client.reserve_volume(self.volume['id'])
        self.assertEqual(202, resp.status)
        # Mark volume which is marked as reserved before
        self.assertRaises(exceptions.BadRequest,
                          self.client.reserve_volume,
                          self.volume['id'])
        # Unmark volume as reserved.
        resp, body = self.client.unreserve_volume(self.volume['id'])
        self.assertEqual(202, resp.status)

    @attr(type=['negative', 'gate'])
    def test_list_volumes_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume-')
        params = {'display_name': v_name}
        resp, fetched_volume = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_volume))

    @attr(type=['negative', 'gate'])
    def test_list_volumes_detail_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume-')
        params = {'display_name': v_name}
        resp, fetched_volume = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_volume))

    @attr(type=['negative', 'gate'])
    def test_list_volumes_with_invalid_status(self):
        params = {'status': 'null'}
        resp, fetched_volume = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_volume))

    @attr(type=['negative', 'gate'])
    def test_list_volumes_detail_with_invalid_status(self):
        params = {'status': 'null'}
        resp, fetched_volume = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_volume))


class VolumesNegativeTestXML(VolumesNegativeTest):
    _interface = 'xml'
