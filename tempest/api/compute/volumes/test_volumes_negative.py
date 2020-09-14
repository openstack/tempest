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

from tempest.api.compute import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesNegativeTest(base.BaseV2ComputeTest):
    """Negative tests of volumes with compute microversion less than 2.36"""

    # These tests will fail with a 404 starting from microversion 2.36. For
    # more information, see:
    # https://docs.openstack.org/api-ref/compute/#volume-extension-os-volumes-os-snapshots-deprecated
    max_microversion = '2.35'

    @classmethod
    def skip_checks(cls):
        super(VolumesNegativeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(VolumesNegativeTest, cls).setup_clients()
        cls.client = cls.volumes_extensions_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c03ea686-905b-41a2-8748-9635154b7c57')
    def test_volume_get_nonexistent_volume_id(self):
        """Test getting details of a non existent volume should fail"""
        # Creating a nonexistent volume id
        # Trying to GET a non existent volume
        self.assertRaises(lib_exc.NotFound, self.client.show_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('54a34226-d910-4b00-9ef8-8683e6c55846')
    def test_volume_delete_nonexistent_volume_id(self):
        """Test deleting a nonexistent volume should fail"""
        # Creating nonexistent volume id
        # Trying to DELETE a non existent volume
        self.assertRaises(lib_exc.NotFound, self.client.delete_volume,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5125ae14-152b-40a7-b3c5-eae15e9022ef')
    def test_create_volume_with_invalid_size(self):
        """Test creating volume with invalid size should fail"""
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('131cb3a1-75cc-4d40-b4c3-1317f64719b0')
    def test_create_volume_without_passing_size(self):
        """Test creating volume without specifying size should fail"""
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8cce995e-0a83-479a-b94d-e1e40b8a09d1')
    def test_create_volume_with_size_zero(self):
        """Test creating volume with size=0 should fail"""
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        metadata = {'Type': 'work'}
        self.assertRaises(lib_exc.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('62bab09a-4c03-4617-8cca-8572bc94af9b')
    def test_get_volume_without_passing_volume_id(self):
        """Test getting volume details without volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.client.show_volume, '')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('62972737-124b-4513-b6cf-2f019f178494')
    def test_delete_invalid_volume_id(self):
        """Test deleting volume with an invalid volume id should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_volume,
                          data_utils.rand_name('invalid'))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0d1417c5-4ae8-4c2c-adc5-5f0b864253e5')
    def test_delete_volume_without_passing_volume_id(self):
        """Test deleting volume without volume id should fail"""
        self.assertRaises(lib_exc.NotFound, self.client.delete_volume, '')
