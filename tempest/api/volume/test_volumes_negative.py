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

import io

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesNegativeTest(base.BaseVolumeTest):
    """Negative tests of volumes"""

    @classmethod
    def resource_setup(cls):
        super(VolumesNegativeTest, cls).resource_setup()

        # Create a test shared instance and volume for attach/detach tests
        cls.volume = cls.create_volume()

    def create_image(self):
        # Create image
        image_name = data_utils.rand_name(self.__class__.__name__ + "-image")
        image = self.images_client.create_image(
            name=image_name,
            container_format=CONF.image.container_formats[0],
            disk_format=CONF.image.disk_formats[0],
            visibility='private',
            min_disk=CONF.volume.volume_size + CONF.volume.volume_size_extend)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.images_client.delete_image, image['id'])

        # Upload image with 1KB data
        image_file = io.BytesIO(data_utils.random_bytes())
        self.images_client.store_image_file(image['id'], image_file)
        waiters.wait_for_image_status(self.images_client,
                                      image['id'], 'active')
        return image

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f131c586-9448-44a4-a8b0-54ca838aa43e')
    def test_volume_get_nonexistent_volume_id(self):
        """Test getting non existent volume should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.show_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('555efa6e-efcd-44ef-8a3b-4a7ca4837a29')
    def test_volume_delete_nonexistent_volume_id(self):
        """Test deleting non existent volume should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.delete_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1ed83a8a-682d-4dfb-a30e-ee63ffd6c049')
    def test_create_volume_with_invalid_size(self):
        """Test creating volume with invalid size should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume, size='#$%')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9387686f-334f-4d31-a439-33494b9e2683')
    def test_create_volume_without_passing_size(self):
        """Test creating volume with empty size should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume, size='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('41331caa-eaf4-4001-869d-bc18c1869360')
    def test_create_volume_with_size_zero(self):
        """Test creating volume with zero size should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume, size='0')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8b472729-9eba-446e-a83b-916bdb34bef7')
    def test_create_volume_with_size_negative(self):
        """Test creating volume with negative size should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume, size='-1')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('10254ed8-3849-454e-862e-3ab8e6aa01d2')
    def test_create_volume_with_nonexistent_volume_type(self):
        """Test creating volume with non existent volume type should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.create_volume,
                          size=CONF.volume.volume_size,
                          volume_type=data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0c36f6ae-4604-4017-b0a9-34fdc63096f9')
    def test_create_volume_with_nonexistent_snapshot_id(self):
        """Test creating volume with non existent snapshot should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.create_volume,
                          size=CONF.volume.volume_size,
                          snapshot_id=data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('47c73e08-4be8-45bb-bfdf-0c4e79b88344')
    def test_create_volume_with_nonexistent_source_volid(self):
        """Test creating volume with non existent source volume should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.create_volume,
                          size=CONF.volume.volume_size,
                          source_volid=data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0186422c-999a-480e-a026-6a665744c30c')
    def test_update_volume_with_nonexistent_volume_id(self):
        """Test updating non existent volume should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.update_volume,
                          volume_id=data_utils.rand_uuid(), name="n")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e66e40d6-65e6-4e75-bdc7-636792fa152d')
    def test_update_volume_with_invalid_volume_id(self):
        """Test updating volume with invalid volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.update_volume,
                          volume_id=data_utils.rand_name('invalid'), name="n")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('72aeca85-57a5-4c1f-9057-f320f9ea575b')
    def test_update_volume_with_empty_volume_id(self):
        """Test updating volume with empty volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.update_volume,
                          volume_id='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('30799cfd-7ee4-446c-b66c-45b383ed211b')
    def test_get_invalid_volume_id(self):
        """Test getting volume with invalid volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.show_volume,
                          data_utils.rand_name('invalid'))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c6c3db06-29ad-4e91-beb0-2ab195fe49e3')
    def test_get_volume_without_passing_volume_id(self):
        """Test getting volume with empty volume id should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.show_volume, '')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1f035827-7c32-4019-9240-b4ec2dbd9dfd')
    def test_delete_invalid_volume_id(self):
        """Test deleting volume with invalid volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.volumes_client.delete_volume,
                          data_utils.rand_name('invalid'))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('441a1550-5d44-4b30-af0f-a6d402f52026')
    def test_delete_volume_without_passing_volume_id(self):
        """Test deleting volume with empty volume id should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.delete_volume, '')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f5e56b0a-5d02-43c1-a2a7-c9b792c2e3f6')
    @utils.services('compute')
    def test_attach_volumes_with_nonexistent_volume_id(self):
        """Test attaching non existent volume to server should fail"""
        server = self.create_server()

        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.attach_volume,
                          data_utils.rand_uuid(),
                          instance_uuid=server['id'],
                          mountpoint="/dev/vdc")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9f9c24e4-011d-46b5-b992-952140ce237a')
    def test_detach_volumes_with_invalid_volume_id(self):
        """Test detaching volume with invalid volume id should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.detach_volume,
                          'xxx')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e0c75c74-ee34-41a9-9288-2a2051452854')
    def test_volume_extend_with_size_smaller_than_original_size(self):
        """Test extending volume with decreasing size should fail"""
        extend_size = 0
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.extend_volume,
                          self.volume['id'], new_size=extend_size)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5d0b480d-e833-439f-8a5a-96ad2ed6f22f')
    def test_volume_extend_with_non_number_size(self):
        """Test extending volume with non-integer size should fail"""
        extend_size = 'abc'
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.extend_volume,
                          self.volume['id'], new_size=extend_size)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('355218f1-8991-400a-a6bb-971239287d92')
    def test_volume_extend_with_None_size(self):
        """Test extending volume with none size should fail"""
        extend_size = None
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.extend_volume,
                          self.volume['id'], new_size=extend_size)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8f05a943-013c-4063-ac71-7baf561e82eb')
    def test_volume_extend_with_nonexistent_volume_id(self):
        """Test extending non existent volume should fail"""
        extend_size = self.volume['size'] + CONF.volume.volume_size_extend
        self.assertRaises(lib_exc.NotFound, self.volumes_client.extend_volume,
                          data_utils.rand_uuid(), new_size=extend_size)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('aff8ba64-6d6f-4f2e-bc33-41a08ee9f115')
    def test_volume_extend_without_passing_volume_id(self):
        """Test extending volume without passing volume id should fail"""
        extend_size = self.volume['size'] + CONF.volume.volume_size_extend
        self.assertRaises(lib_exc.NotFound, self.volumes_client.extend_volume,
                          None, new_size=extend_size)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ac6084c0-0546-45f9-b284-38a367e0e0e2')
    def test_reserve_volume_with_nonexistent_volume_id(self):
        """Test reserving non existent volume should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.reserve_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('eb467654-3dc1-4a72-9b46-47c29d22654c')
    def test_unreserve_volume_with_nonexistent_volume_id(self):
        """Test unreserving non existent volume should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.volumes_client.unreserve_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('449c4ed2-ecdd-47bb-98dc-072aeccf158c')
    def test_reserve_volume_with_negative_volume_status(self):
        """Test reserving already reserved volume should fail"""
        # Mark volume as reserved.
        self.volumes_client.reserve_volume(self.volume['id'])
        # Mark volume which is marked as reserved before
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.reserve_volume,
                          self.volume['id'])
        # Unmark volume as reserved.
        self.volumes_client.unreserve_volume(self.volume['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0f4aa809-8c7b-418f-8fb3-84c7a5dfc52f')
    def test_list_volumes_with_nonexistent_name(self):
        """Test listing volumes with non existent name should get nothing"""
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        params = {'name': v_name}
        fetched_volume = self.volumes_client.list_volumes(
            params=params)['volumes']
        self.assertEmpty(fetched_volume)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9ca17820-a0e7-4cbd-a7fa-f4468735e359')
    def test_list_volumes_detail_with_nonexistent_name(self):
        """Test listing volume details with non existent name

        Listing volume details with non existent name should get nothing.
        """
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        params = {'name': v_name}
        fetched_volume = \
            self.volumes_client.list_volumes(
                detail=True, params=params)['volumes']
        self.assertEmpty(fetched_volume)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('143b279b-7522-466b-81be-34a87d564a7c')
    def test_list_volumes_with_invalid_status(self):
        """Test listing volumes with invalid status should get nothing"""
        params = {'status': 'null'}
        fetched_volume = self.volumes_client.list_volumes(
            params=params)['volumes']
        self.assertEmpty(fetched_volume)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ba94b27b-be3f-496c-a00e-0283b373fa75')
    def test_list_volumes_detail_with_invalid_status(self):
        """Test listing volume details with invalid status

        Listing volume details with invalid status should get nothing
        """
        params = {'status': 'null'}
        fetched_volume = \
            self.volumes_client.list_volumes(detail=True,
                                             params=params)['volumes']
        self.assertEmpty(fetched_volume)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5b810c91-0ad1-47ce-aee8-615f789be78f')
    @utils.services('image')
    def test_create_volume_from_image_with_decreasing_size(self):
        """Test creating volume from image with decreasing size should fail"""
        # Create image
        image = self.create_image()

        # Note(jeremyZ): To shorten the test time (uploading a big size image
        # is time-consuming), here just consider the scenario that volume size
        # is smaller than the min_disk of image.
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume,
                          size=CONF.volume.volume_size,
                          imageRef=image['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d15e7f35-2cfc-48c8-9418-c8223a89bcbb')
    @utils.services('image')
    def test_create_volume_from_deactivated_image(self):
        """Test creating volume from deactivated image should fail"""
        # Create image
        image = self.create_image()

        # Deactivate the image
        self.images_client.deactivate_image(image['id'])
        body = self.images_client.show_image(image['id'])
        self.assertEqual("deactivated", body['status'])
        # Try creating a volume from deactivated image
        self.assertRaises(lib_exc.BadRequest,
                          self.create_volume,
                          imageRef=image['id'])
