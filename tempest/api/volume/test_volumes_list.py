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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from testtools import matchers

from tempest.api.volume import base
from tempest import test

LOG = logging.getLogger(__name__)


class VolumesV2ListTestJSON(base.BaseVolumeTest):

    """
    This test creates a number of 1G volumes. To run successfully,
    ensure that the backing file for the volume group that Nova uses
    has space for at least 3 1G volumes!
    If you are running a Devstack environment, ensure that the
    VOLUME_BACKING_FILE_SIZE is at least 4G in your localrc
    """

    VOLUME_FIELDS = ('id', 'name')

    def assertVolumesIn(self, fetched_list, expected_list, fields=None):
        if fields:
            expected_list = map(operator.itemgetter(*fields), expected_list)
            fetched_list = map(operator.itemgetter(*fields), fetched_list)

        missing_vols = [v for v in expected_list if v not in fetched_list]
        if len(missing_vols) == 0:
            return

        def str_vol(vol):
            return "%s:%s" % (vol['id'], vol[self.name])

        raw_msg = "Could not find volumes %s in expected list %s; fetched %s"
        self.fail(raw_msg % ([str_vol(v) for v in missing_vols],
                             [str_vol(v) for v in expected_list],
                             [str_vol(v) for v in fetched_list]))

    @classmethod
    def setup_clients(cls):
        super(VolumesV2ListTestJSON, cls).setup_clients()
        cls.client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(VolumesV2ListTestJSON, cls).resource_setup()
        cls.name = cls.VOLUME_FIELDS[1]

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

    def _list_by_param_value_and_assert(self, params, with_detail=False):
        """
        Perform list or list_details action with given params
        and validates result.
        """
        if with_detail:
            fetched_vol_list = \
                self.client.list_volumes(detail=True, params=params)
        else:
            fetched_vol_list = self.client.list_volumes(params=params)

        # Validating params of fetched volumes
        # In v2, only list detail view includes items in params.
        # In v1, list view and list detail view are same. So the
        # following check should be run when 'with_detail' is True
        # or v1 tests.
        if with_detail or self._api_version == 1:
            for volume in fetched_vol_list:
                for key in params:
                    msg = "Failed to list volumes %s by %s" % \
                          ('details' if with_detail else '', key)
                    if key == 'metadata':
                        self.assertThat(
                            volume[key].items(),
                            matchers.ContainsAll(params[key].items()),
                            msg)
                    else:
                        self.assertEqual(params[key], volume[key], msg)

    @test.attr(type='smoke')
    @test.idempotent_id('0b6ddd39-b948-471f-8038-4787978747c4')
    def test_volume_list(self):
        # Get a list of Volumes
        # Fetch all volumes
        fetched_list = self.client.list_volumes()
        self.assertVolumesIn(fetched_list, self.volume_list,
                             fields=self.VOLUME_FIELDS)

    @test.attr(type='gate')
    @test.idempotent_id('adcbb5a7-5ad8-4b61-bd10-5380e111a877')
    def test_volume_list_with_details(self):
        # Get a list of Volumes with details
        # Fetch all Volumes
        fetched_list = self.client.list_volumes(detail=True)
        self.assertVolumesIn(fetched_list, self.volume_list)

    @test.attr(type='gate')
    @test.idempotent_id('a28e8da4-0b56-472f-87a8-0f4d3f819c02')
    def test_volume_list_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {self.name: volume[self.name]}
        fetched_vol = self.client.list_volumes(params=params)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0][self.name],
                         volume[self.name])

    @test.attr(type='gate')
    @test.idempotent_id('2de3a6d4-12aa-403b-a8f2-fdeb42a89623')
    def test_volume_list_details_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {self.name: volume[self.name]}
        fetched_vol = self.client.list_volumes(detail=True, params=params)
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0][self.name],
                         volume[self.name])

    @test.attr(type='gate')
    @test.idempotent_id('39654e13-734c-4dab-95ce-7613bf8407ce')
    def test_volumes_list_by_status(self):
        params = {'status': 'available'}
        fetched_list = self.client.list_volumes(params=params)
        self._list_by_param_value_and_assert(params)
        self.assertVolumesIn(fetched_list, self.volume_list,
                             fields=self.VOLUME_FIELDS)

    @test.attr(type='gate')
    @test.idempotent_id('2943f712-71ec-482a-bf49-d5ca06216b9f')
    def test_volumes_list_details_by_status(self):
        params = {'status': 'available'}
        fetched_list = self.client.list_volumes(detail=True, params=params)
        for volume in fetched_list:
            self.assertEqual('available', volume['status'])
        self.assertVolumesIn(fetched_list, self.volume_list)

    @test.attr(type='gate')
    @test.idempotent_id('c0cfa863-3020-40d7-b587-e35f597d5d87')
    def test_volumes_list_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        fetched_list = self.client.list_volumes(params=params)
        self._list_by_param_value_and_assert(params)
        self.assertVolumesIn(fetched_list, self.volume_list,
                             fields=self.VOLUME_FIELDS)

    @test.attr(type='gate')
    @test.idempotent_id('e1b80d13-94f0-4ba2-a40e-386af29f8db1')
    def test_volumes_list_details_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        fetched_list = self.client.list_volumes(detail=True, params=params)
        for volume in fetched_list:
            self.assertEqual(zone, volume['availability_zone'])
        self.assertVolumesIn(fetched_list, self.volume_list)

    @test.attr(type='gate')
    @test.idempotent_id('b5ebea1b-0603-40a0-bb41-15fcd0a53214')
    def test_volume_list_with_param_metadata(self):
        # Test to list volumes when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    @test.idempotent_id('1ca92d3c-4a8e-4b43-93f5-e4c7fb3b291d')
    def test_volume_list_with_detail_param_metadata(self):
        # Test to list volumes details when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    @test.idempotent_id('777c87c1-2fc4-4883-8b8e-5c0b951d1ec8')
    def test_volume_list_param_display_name_and_status(self):
        # Test to list volume when display name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {self.name: volume[self.name],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    @test.idempotent_id('856ab8ca-6009-4c37-b691-be1065528ad4')
    def test_volume_list_with_detail_param_display_name_and_status(self):
        # Test to list volume when name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {self.name: volume[self.name],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params, with_detail=True)


class VolumesV1ListTestJSON(VolumesV2ListTestJSON):
    _api_version = 1
    VOLUME_FIELDS = ('id', 'display_name')
