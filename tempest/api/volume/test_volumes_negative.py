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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.volume import base
from tempest import test


class VolumesV2NegativeTest(base.BaseVolumeTest):

    @classmethod
    def setup_clients(cls):
        super(VolumesV2NegativeTest, cls).setup_clients()
        cls.client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(VolumesV2NegativeTest, cls).resource_setup()

        cls.name_field = cls.special_fields['name_field']

        # Create a test shared instance and volume for attach/detach tests
        cls.volume = cls.create_volume()
        cls.mountpoint = "/dev/vdc"

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f131c586-9448-44a4-a8b0-54ca838aa43e')
    def test_volume_get_nonexistent_volume_id(self):
        # Should not be able to get a non-existent volume
        self.assertRaises(lib_exc.NotFound, self.client.show_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('555efa6e-efcd-44ef-8a3b-4a7ca4837a29')
    def test_volume_delete_nonexistent_volume_id(self):
        # Should not be able to delete a non-existent Volume
        self.assertRaises(lib_exc.NotFound, self.client.delete_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('1ed83a8a-682d-4dfb-a30e-ee63ffd6c049')
    def test_create_volume_with_invalid_size(self):
        # Should not be able to create volume with invalid size
        # in request
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9387686f-334f-4d31-a439-33494b9e2683')
    def test_create_volume_with_out_passing_size(self):
        # Should not be able to create volume without passing size
        # in request
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('41331caa-eaf4-4001-869d-bc18c1869360')
    def test_create_volume_with_size_zero(self):
        # Should not be able to create volume with size zero
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('8b472729-9eba-446e-a83b-916bdb34bef7')
    def test_create_volume_with_size_negative(self):
        # Should not be able to create volume with size negative
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='-1', display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('10254ed8-3849-454e-862e-3ab8e6aa01d2')
    def test_create_volume_with_nonexistent_volume_type(self):
        # Should not be able to create volume with non-existent volume type
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.create_volume,
                          size='1', volume_type=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0c36f6ae-4604-4017-b0a9-34fdc63096f9')
    def test_create_volume_with_nonexistent_snapshot_id(self):
        # Should not be able to create volume with non-existent snapshot
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.create_volume,
                          size='1', snapshot_id=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('47c73e08-4be8-45bb-bfdf-0c4e79b88344')
    def test_create_volume_with_nonexistent_source_volid(self):
        # Should not be able to create volume with non-existent source volume
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.create_volume,
                          size='1', source_volid=str(uuid.uuid4()),
                          display_name=v_name, metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0186422c-999a-480e-a026-6a665744c30c')
    def test_update_volume_with_nonexistent_volume_id(self):
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.update_volume,
                          volume_id=str(uuid.uuid4()), display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e66e40d6-65e6-4e75-bdc7-636792fa152d')
    def test_update_volume_with_invalid_volume_id(self):
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.update_volume,
                          volume_id='#$%%&^&^', display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('72aeca85-57a5-4c1f-9057-f320f9ea575b')
    def test_update_volume_with_empty_volume_id(self):
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.NotFound, self.client.update_volume,
                          volume_id='', display_name=v_name,
                          metadata=metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('30799cfd-7ee4-446c-b66c-45b383ed211b')
    def test_get_invalid_volume_id(self):
        # Should not be able to get volume with invalid id
        self.assertRaises(lib_exc.NotFound, self.client.show_volume,
                          '#$%%&^&^')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('c6c3db06-29ad-4e91-beb0-2ab195fe49e3')
    def test_get_volume_without_passing_volume_id(self):
        # Should not be able to get volume when empty ID is passed
        self.assertRaises(lib_exc.NotFound, self.client.show_volume, '')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('1f035827-7c32-4019-9240-b4ec2dbd9dfd')
    def test_delete_invalid_volume_id(self):
        # Should not be able to delete volume when invalid ID is passed
        self.assertRaises(lib_exc.NotFound, self.client.delete_volume,
                          '!@#$%^&*()')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('441a1550-5d44-4b30-af0f-a6d402f52026')
    def test_delete_volume_without_passing_volume_id(self):
        # Should not be able to delete volume when empty ID is passed
        self.assertRaises(lib_exc.NotFound, self.client.delete_volume, '')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f5e56b0a-5d02-43c1-a2a7-c9b792c2e3f6')
    @test.services('compute')
    def test_attach_volumes_with_nonexistent_volume_id(self):
        srv_name = data_utils.rand_name('Instance')
        server = self.create_server(srv_name)
        self.addCleanup(self.servers_client.delete_server, server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        self.assertRaises(lib_exc.NotFound,
                          self.client.attach_volume,
                          str(uuid.uuid4()),
                          server['id'],
                          self.mountpoint)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9f9c24e4-011d-46b5-b992-952140ce237a')
    def test_detach_volumes_with_invalid_volume_id(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.detach_volume,
                          'xxx')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e0c75c74-ee34-41a9-9288-2a2051452854')
    def test_volume_extend_with_size_smaller_than_original_size(self):
        # Extend volume with smaller size than original size.
        extend_size = 0
        self.assertRaises(lib_exc.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('5d0b480d-e833-439f-8a5a-96ad2ed6f22f')
    def test_volume_extend_with_non_number_size(self):
        # Extend volume when size is non number.
        extend_size = 'abc'
        self.assertRaises(lib_exc.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('355218f1-8991-400a-a6bb-971239287d92')
    def test_volume_extend_with_None_size(self):
        # Extend volume with None size.
        extend_size = None
        self.assertRaises(lib_exc.BadRequest, self.client.extend_volume,
                          self.volume['id'], extend_size)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('8f05a943-013c-4063-ac71-7baf561e82eb')
    def test_volume_extend_with_nonexistent_volume_id(self):
        # Extend volume size when volume is nonexistent.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(lib_exc.NotFound, self.client.extend_volume,
                          str(uuid.uuid4()), extend_size)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('aff8ba64-6d6f-4f2e-bc33-41a08ee9f115')
    def test_volume_extend_without_passing_volume_id(self):
        # Extend volume size when passing volume id is None.
        extend_size = int(self.volume['size']) + 1
        self.assertRaises(lib_exc.NotFound, self.client.extend_volume,
                          None, extend_size)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ac6084c0-0546-45f9-b284-38a367e0e0e2')
    def test_reserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.reserve_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('eb467654-3dc1-4a72-9b46-47c29d22654c')
    def test_unreserve_volume_with_nonexistent_volume_id(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.unreserve_volume,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('449c4ed2-ecdd-47bb-98dc-072aeccf158c')
    def test_reserve_volume_with_negative_volume_status(self):
        # Mark volume as reserved.
        self.client.reserve_volume(self.volume['id'])
        # Mark volume which is marked as reserved before
        self.assertRaises(lib_exc.BadRequest,
                          self.client.reserve_volume,
                          self.volume['id'])
        # Unmark volume as reserved.
        self.client.unreserve_volume(self.volume['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0f4aa809-8c7b-418f-8fb3-84c7a5dfc52f')
    def test_list_volumes_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume')
        params = {self.name_field: v_name}
        fetched_volume = self.client.list_volumes(params=params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9ca17820-a0e7-4cbd-a7fa-f4468735e359')
    def test_list_volumes_detail_with_nonexistent_name(self):
        v_name = data_utils.rand_name('Volume')
        params = {self.name_field: v_name}
        fetched_volume = \
            self.client.list_volumes(detail=True, params=params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('143b279b-7522-466b-81be-34a87d564a7c')
    def test_list_volumes_with_invalid_status(self):
        params = {'status': 'null'}
        fetched_volume = self.client.list_volumes(params=params)
        self.assertEqual(0, len(fetched_volume))

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ba94b27b-be3f-496c-a00e-0283b373fa75')
    def test_list_volumes_detail_with_invalid_status(self):
        params = {'status': 'null'}
        fetched_volume = \
            self.client.list_volumes(detail=True, params=params)
        self.assertEqual(0, len(fetched_volume))


class VolumesV1NegativeTest(VolumesV2NegativeTest):
    _api_version = 1
    _name = 'display_name'
