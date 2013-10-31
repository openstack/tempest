# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest.test import attr

LOG = logging.getLogger(__name__)


class VolumesListTest(base.BaseVolumeTest):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is at least 4G in your localrc
    """

    _interface = 'json'

    def assertVolumesIn(self, fetched_list, expected_list):
        missing_vols = [v for v in expected_list if v not in fetched_list]
        if len(missing_vols) == 0:
            return

        def str_vol(vol):
            return "%s:%s" % (vol['id'], vol['display_name'])

        raw_msg = "Could not find volumes %s in expected list %s; fetched %s"
        self.fail(raw_msg % ([str_vol(v) for v in missing_vols],
                             [str_vol(v) for v in expected_list],
                             [str_vol(v) for v in fetched_list]))

    @classmethod
    def setUpClass(cls):
        super(VolumesListTest, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create 3 test volumes
        cls.volume_list = []
        cls.volume_id_list = []
        for i in range(3):
            v_name = data_utils.rand_name('volume')
            metadata = {'Type': 'work'}
            try:
                resp, volume = cls.client.create_volume(size=1,
                                                        display_name=v_name,
                                                        metadata=metadata)
                cls.client.wait_for_volume_status(volume['id'], 'available')
                resp, volume = cls.client.get_volume(volume['id'])
                cls.volume_list.append(volume)
                cls.volume_id_list.append(volume['id'])
            except Exception as exc:
                LOG.exception(exc)
                if cls.volume_list:
                    # We could not create all the volumes, though we were able
                    # to create *some* of the volumes. This is typically
                    # because the backing file size of the volume group is
                    # too small.
                    for volid in cls.volume_id_list:
                        cls.client.delete_volume(volid)
                        cls.client.wait_for_resource_deletion(volid)
                raise exc

    @classmethod
    def tearDownClass(cls):
        # Delete the created volumes
        for volid in cls.volume_id_list:
            resp, _ = cls.client.delete_volume(volid)
            cls.client.wait_for_resource_deletion(volid)
        super(VolumesListTest, cls).tearDownClass()

    @attr(type='smoke')
    def test_volume_list(self):
        # Get a list of Volumes
        # Fetch all volumes
        resp, fetched_list = self.client.list_volumes()
        self.assertEqual(200, resp.status)
        self.assertVolumesIn(fetched_list, self.volume_list)

    @attr(type='gate')
    def test_volume_list_with_details(self):
        # Get a list of Volumes with details
        # Fetch all Volumes
        resp, fetched_list = self.client.list_volumes_with_detail()
        self.assertEqual(200, resp.status)
        self.assertVolumesIn(fetched_list, self.volume_list)

    @attr(type='gate')
    def test_volume_list_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'display_name': volume['display_name']}
        resp, fetched_vol = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['display_name'],
                         volume['display_name'])

    @attr(type='gate')
    def test_volume_list_details_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'display_name': volume['display_name']}
        resp, fetched_vol = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['display_name'],
                         volume['display_name'])

    @attr(type='gate')
    def test_volumes_list_by_status(self):
        params = {'status': 'available'}
        resp, fetched_list = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        for volume in fetched_list:
            self.assertEqual('available', volume['status'])
        self.assertVolumesIn(fetched_list, self.volume_list)

    @attr(type='gate')
    def test_volumes_list_details_by_status(self):
        params = {'status': 'available'}
        resp, fetched_list = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        for volume in fetched_list:
            self.assertEqual('available', volume['status'])
        self.assertVolumesIn(fetched_list, self.volume_list)

    @attr(type='gate')
    def test_volumes_list_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        resp, fetched_list = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        for volume in fetched_list:
            self.assertEqual(zone, volume['availability_zone'])
        self.assertVolumesIn(fetched_list, self.volume_list)

    @attr(type='gate')
    def test_volumes_list_details_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        resp, fetched_list = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        for volume in fetched_list:
            self.assertEqual(zone, volume['availability_zone'])
        self.assertVolumesIn(fetched_list, self.volume_list)


class VolumeListTestXML(VolumesListTest):
    _interface = 'xml'
