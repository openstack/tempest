# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from tempest.api.volume import base
from tempest import test


class VolumesV2ListTestJSON(base.BaseVolumeTest):

    """
    volumes v2 specific tests.

    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is at least 4G in your localrc
    """

    @classmethod
    def setup_clients(cls):
        super(VolumesV2ListTestJSON, cls).setup_clients()
        cls.client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(VolumesV2ListTestJSON, cls).resource_setup()

        # Create 3 test volumes
        cls.volume_list = []
        cls.volume_id_list = []
        cls.metadata = {'Type': 'work'}
        for i in range(3):
            volume = cls.create_volume(metadata=cls.metadata)
            volume = cls.client.show_volume(volume['id'])
            cls.volume_list.append(volume)
            cls.volume_id_list.append(volume['id'])

    @classmethod
    def resource_cleanup(cls):
        # Delete the created volumes
        for volid in cls.volume_id_list:
            cls.client.delete_volume(volid)
            cls.client.wait_for_resource_deletion(volid)
        super(VolumesV2ListTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    @test.idempotent_id('2a7064eb-b9c3-429b-b888-33928fc5edd3')
    def test_volume_list_details_with_multiple_params(self):
        # List volumes detail using combined condition
        def _list_details_with_multiple_params(limit=2,
                                               status='available',
                                               sort_dir='asc',
                                               sort_key='id'):
            params = {'limit': limit,
                      'status': status,
                      'sort_dir': sort_dir,
                      'sort_key': sort_key
                      }
            fetched_volume = self.client.list_volumes(detail=True,
                                                      params=params)
            self.assertEqual(limit, len(fetched_volume),
                             "The count of volumes is %s, expected:%s " %
                             (len(fetched_volume), limit))
            self.assertEqual(status, fetched_volume[0]['status'])
            self.assertEqual(status, fetched_volume[1]['status'])
            val0 = fetched_volume[0][sort_key]
            val1 = fetched_volume[1][sort_key]
            if sort_dir == 'asc':
                self.assertTrue(val0 < val1,
                                "%s < %s" % (val0, val1))
            elif sort_dir == 'desc':
                self.assertTrue(val0 > val1,
                                "%s > %s" % (val0, val1))

        _list_details_with_multiple_params()
        _list_details_with_multiple_params(sort_dir='desc')
