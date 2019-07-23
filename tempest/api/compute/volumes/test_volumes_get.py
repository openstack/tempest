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

from testtools import matchers

from tempest.api.compute import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


CONF = config.CONF


class VolumesGetTestJSON(base.BaseV2ComputeTest):

    # These tests will fail with a 404 starting from microversion 2.36. For
    # more information, see:
    # https://docs.openstack.org/api-ref/compute/#volume-extension-os-volumes-os-snapshots-deprecated
    max_microversion = '2.35'

    @classmethod
    def skip_checks(cls):
        super(VolumesGetTestJSON, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(VolumesGetTestJSON, cls).setup_clients()
        cls.volumes_client = cls.volumes_extensions_client

    @decorators.idempotent_id('f10f25eb-9775-4d9d-9cbe-1cf54dae9d5f')
    def test_volume_create_get_delete(self):
        # CREATE, GET, DELETE Volume
        v_name = data_utils.rand_name(self.__class__.__name__ + '-Volume')
        metadata = {'Type': 'work'}
        # Create volume
        volume = self.create_volume(size=CONF.volume.volume_size,
                                    display_name=v_name,
                                    metadata=metadata)
        self.assertEqual(volume['displayName'], v_name,
                         "The created volume name is not equal "
                         "to the requested name")
        # GET Volume
        fetched_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        # Verification of details of fetched Volume
        self.assertEqual(v_name,
                         fetched_volume['displayName'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertEqual(CONF.volume.volume_size,
                         fetched_volume['size'],
                         'The fetched volume size is different '
                         'from the created Volume')
        self.assertEqual(volume['id'],
                         fetched_volume['id'],
                         'The fetched Volume is different '
                         'from the created Volume')
        self.assertThat(fetched_volume['metadata'].items(),
                        matchers.ContainsAll(metadata.items()),
                        'The fetched Volume metadata misses data '
                        'from the created Volume')
