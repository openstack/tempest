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

from tempest_lib.common.utils import data_utils
from testtools import matchers

from tempest.api.compute import base
from tempest import config
from tempest import test


CONF = config.CONF


class VolumesGetTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesGetTestJSON, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(VolumesGetTestJSON, cls).setup_clients()
        cls.client = cls.volumes_extensions_client

    @test.attr(type='smoke')
    @test.idempotent_id('f10f25eb-9775-4d9d-9cbe-1cf54dae9d5f')
    def test_volume_create_get_delete(self):
        # CREATE, GET, DELETE Volume
        volume = None
        v_name = data_utils.rand_name('Volume')
        metadata = {'Type': 'work'}
        # Create volume
        volume = self.client.create_volume(display_name=v_name,
                                           metadata=metadata)
        self.addCleanup(self.delete_volume, volume['id'])
        self.assertIn('id', volume)
        self.assertIn('displayName', volume)
        self.assertEqual(volume['displayName'], v_name,
                         "The created volume name is not equal "
                         "to the requested name")
        self.assertTrue(volume['id'] is not None,
                        "Field volume id is empty or not found.")
        # Wait for Volume status to become ACTIVE
        self.client.wait_for_volume_status(volume['id'], 'available')
        # GET Volume
        fetched_volume = self.client.get_volume(volume['id'])
        # Verification of details of fetched Volume
        self.assertEqual(v_name,
                         fetched_volume['displayName'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(volume['id'],
                         fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertThat(fetched_volume['metadata'].items(),
                        matchers.ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')
