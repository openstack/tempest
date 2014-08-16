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
from tempest import test


class VolumesV2NegativeTest(base.BaseVolumeTest):

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumesV2NegativeTest, cls).setUpClass()
        cls.client = cls.volumes_client

        cls.name_field = cls.special_fields['name_field']

        # Create a test shared instance and volume for attach/detach tests
        cls.volume = cls.create_volume()
        cls.mountpoint = "/dev/vdc"

    @test.attr(type=['negative', 'gate'])
    def test_volume_get_nonexistent_volume_id(self):
        # Should not be able to get a non-existent volume
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_volume_delete_nonexistent_volume_id(self):
        # Should not be able to delete a non-existent Volume
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_invalid_size(self):
        # Should not be able to create volume with invalid size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_out_passing_size(self):
        # Should not be able to create volume without passing size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_size_zero(self):
        # Should not be able to create volume with size zero
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_size_negative(self):
        # Should not be able to create volume with size negative
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='-1', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistent_volume_type(self):
        # Should not be able to create volume with non-existent volume type
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', volume_type=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistent_snapshot_id(self):
        # Should not be able to create volume with non-existent snapshot
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', snapshot_id=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_create_volume_with_nonexistent_source_volid(self):
        # Should not be able to create volume with non-existent source volume
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.create_volume,
                          size='1', source_volid=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_update_volume_with_nonexistent_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id=str(uuid.uuid4()), display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_update_volume_with_invalid_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id='#$%%&^&^', display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_update_volume_with_empty_volume_id(self):
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.NotFound, self.client.update_volume,
                          volume_id='', display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    def test_get_invalid_volume_id(self):
        # Should not be able to get volume with invalid id
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          '#$%%&^&^')

    @test.attr(type=['negative', 'gate'])
    def test_get_volume_without_passing_volume_id(self):
        # Should not be able to get volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.get_volume, '')

    @test.attr(type=['negative', 'gate'])
    def test_delete_invalid_volume_id(self):
        # Should not be able to delete volume when invalid ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          '!@#$%^&*()')

    @test.attr(type=['negative', 'gate'])
    def test_delete_volume_without_passing_volume_id(self):
        # Should not be able to delete volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume, '')

    @test.attr(type=['negative', 'gate'])
    @test.services('compute')
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

    @test.attr(type=['negative', 'gate'])
    def test_detach_volumes_with_invalid_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.detach_volume,
                          'xxx')

    @test.attr(type=['negative', 'gate'])
    def test_volume_extend_with_size_smaller_than_original_size(self):
        # Extend volume with smaller size than original size.
        extend_size = 0
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    def test_volume_extend_with_non_number_size(self):
        # Extend volume when size is non number.
        extend_size = 'abc'
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    def test_volume_extend_with_None_size(self):
        # Extend volume with None size.
        extend_size = None
        self.assertRaises(exceptions.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    def test_volume_extend_with_nonexistent_volume_id(self):
        # Extend volume size when volume is nonexistent.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(exceptions.NotFound, self.client.extend_volume,
                          str(uuid.uuid4()), extend_size)

    @test.attr(type=['negative', 'gate'])
    def test_volume_extend_without_passing_volume_id(self):
        # Extend volume size when passing volume id is None.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(exceptions.NotFound, self.client.extend_volume,
                          None, extend_size)

    @test.attr(type=['negative', 'gate'])
    def test_reserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.reserve_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_unreserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.unreserve_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_reserve_volume_with_negative_volume_status(self):
        # Mark volume as reserved.
        _, body = self.client.reserve_volume(self.volume['id'])
        # Mark volume which is marked as reserved before
        self.assertRaises(exceptions.BadRequest,
                          self.client.reserve_volume,
                          self.volume['id'])
        # Unmark volume as reserved.
        _, body = self.client.unreserve_volume(self.volume['id'])

    @test.attr(type=['negative', 'gate'])
    def test_list_volumes_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume-')
        params = {self.name_field: v_name}
        _, fetched_volume = self.client.list_volumes(params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    def test_list_volumes_detail_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume-')
        params = {self.name_field: v_name}
        _, fetched_volume = self.client.list_volumes_with_detail(params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    def test_list_volumes_with_invalid_status(self):
        params = {'status': 'null'}
        _, fetched_volume = self.client.list_volumes(params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    def test_list_volumes_detail_with_invalid_status(self):
        params = {'status': 'null'}
        _, fetched_volume = self.client.list_volumes_with_detail(params)
        self.assertEqual(0, len(fetched_volume))


class VolumesV2NegativeTestXML(VolumesV2NegativeTest):
    _interface = 'xml'


class VolumesV1NegativeTest(VolumesV2NegativeTest):
    _api_version = 1
    _name = 'display_name'


class VolumesV1NegativeTestXML(VolumesV1NegativeTest):
    _interface = 'xml'
