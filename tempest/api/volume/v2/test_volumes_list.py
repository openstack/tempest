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
import operator

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest import test
from testtools import matchers

LOG = logging.getLogger(__name__)

VOLUME_FIELDS = ('id', 'name')


class VolumesV2ListTestJSON(base.BaseVolumeV2Test):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is at least 4G in your localrc
    """

    _interface = 'json'

    def assertVolumesIn(self, fetched_list, expected_list, fields=None):
        if fields:
            expected_list = map(operator.itemgetter(*fields), expected_list)
            fetched_list = map(operator.itemgetter(*fields), fetched_list)

        missing_vols = [v for v in expected_list if v not in fetched_list]
        if len(missing_vols) == 0:
            return

        def str_vol(vol):
            return "%s:%s" % (vol['id'], vol['name'])

        raw_msg = "Could not find volumes %s in expected list %s; fetched %s"
        self.fail(raw_msg % ([str_vol(v) for v in missing_vols],
                             [str_vol(v) for v in expected_list],
                             [str_vol(v) for v in fetched_list]))

    @classmethod
    def setUpClass(cls):
        super(VolumesV2ListTestJSON, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create 3 test volumes
        cls.volume_list = []
        cls.volume_id_list = []
        cls.metadata = {'Type': 'work'}
        for i in range(3):
            try:
                volume = cls.create_volume(metadata=cls.metadata)
                resp, volume = cls.client.get_volume(volume['id'])
                cls.volume_list.append(volume)
                cls.volume_id_list.append(volume['id'])
            except Exception:
                LOG.exception('Failed to create volume. %d volumes were '
                              'created' % len(cls.volume_id_list))
                if cls.volume_list:
                    # We could not create all the volumes, though we were able
                    # to create *some* of the volumes. This is typically
                    # because the backing file size of the volume group is
                    # too small.
                    for volid in cls.volume_id_list:
                        cls.client.delete_volume(volid)
                        cls.client.wait_for_resource_deletion(volid)
                raise

    @classmethod
    def tearDownClass(cls):
        # Delete the created volumes
        for volid in cls.volume_id_list:
            resp, _ = cls.client.delete_volume(volid)
            cls.client.wait_for_resource_deletion(volid)
        super(VolumesV2ListTestJSON, cls).tearDownClass()

    def _list_by_param_value_and_assert(self, params, expected_list=None,
                                        with_detail=False):
        """
        Perform list or list_details action with given params
        and validates result.
        """
        if with_detail:
            resp, fetched_vol_list = \
                self.client.list_volumes_with_detail(params=params)
        else:
            resp, fetched_vol_list = self.client.list_volumes(params=params)

        self.assertEqual(200, resp.status)
        if expected_list is None:
            expected_list = self.volume_list
        self.assertVolumesIn(fetched_vol_list, expected_list,
                             fields=VOLUME_FIELDS)
        # Validating params of fetched volumes
        if with_detail:
            for volume in fetched_vol_list:
                for key in params:
                    msg = "Failed to list volumes %s by %s" % \
                          ('details' if with_detail else '', key)
                    if key == 'metadata':
                        self.assertThat(volume[key].items(),
                                        matchers.ContainsAll(
                                            params[key].items()), msg)
                    else:
                        self.assertEqual(params[key], volume[key], msg)

    @test.attr(type='smoke')
    def test_volume_list(self):
        # Get a list of Volumes
        # Fetch all volumes
        resp, fetched_list = self.client.list_volumes()
        self.assertEqual(200, resp.status)
        self.assertVolumesIn(fetched_list, self.volume_list,
                             fields=VOLUME_FIELDS)

    @test.attr(type='gate')
    def test_volume_list_with_details(self):
        # Get a list of Volumes with details
        # Fetch all Volumes
        resp, fetched_list = self.client.list_volumes_with_detail()
        self.assertEqual(200, resp.status)
        self.assertVolumesIn(fetched_list, self.volume_list)

    @test.attr(type='gate')
    def test_volume_list_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name']}
        resp, fetched_vol = self.client.list_volumes(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['name'], volume['name'])

    @test.attr(type='gate')
    def test_volume_list_details_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name']}
        resp, fetched_vol = self.client.list_volumes_with_detail(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['name'], volume['name'])

    @test.attr(type='gate')
    def test_volumes_list_by_status(self):
        params = {'status': 'available'}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_volumes_list_details_by_status(self):
        params = {'status': 'available'}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    def test_volumes_list_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_volumes_list_details_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    def test_volume_list_with_param_metadata(self):
        # Test to list volumes when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_volume_list_with_detail_param_metadata(self):
        # Test to list volumes details when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    def test_volume_list_param_display_name_and_status(self):
        # Test to list volume when display name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name'],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params, expected_list=[volume])

    @test.attr(type='gate')
    def test_volume_list_with_detail_param_display_name_and_status(self):
        # Test to list volume when name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name'],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params, expected_list=[volume],
                                             with_detail=True)


class VolumesV2ListTestXML(VolumesV2ListTestJSON):
    _interface = 'xml'
