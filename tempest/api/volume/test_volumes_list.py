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
import random

from six.moves.urllib import parse
from testtools import matchers

from tempest.api.volume import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class VolumesListTestJSON(base.BaseVolumeTest):
    # NOTE: This test creates a number of 1G volumes. To run it successfully,
    # ensure that the backing file for the volume group that Cinder uses
    # has space for at least 3 1G volumes!
    # If you are running a Devstack environment, ensure that the
    # VOLUME_BACKING_FILE_SIZE is at least 4G in your localrc

    VOLUME_FIELDS = ('id', 'name')

    @classmethod
    def _remove_volatile_fields(cls, fetched_list):
        """Remove fields that should not be compared.

        This method makes sure that Tempest does not compare e.g.
        the volume's "updated_at" field that may change for any reason
        internal to the operation of Cinder.
        """
        for volume in fetched_list:
            for field in ('updated_at',):
                if field in volume:
                    del volume[field]

    def _assert_volumes_in(self, fetched_list, expected_list, fields=None):
        """Check out the list.

        This function is aim at check out whether all of the volumes in
        expected_list are in fetched_list.
        """
        if fields:
            fieldsgetter = operator.itemgetter(*fields)
            expected_list = map(fieldsgetter, expected_list)
            fetched_list = [fieldsgetter(item) for item in fetched_list]

        # Hopefully the expected_list has already been cleaned.
        self._remove_volatile_fields(fetched_list)
        missing_vols = [v for v in expected_list if v not in fetched_list]
        if not missing_vols:
            return

        def str_vol(vol):
            return "%s:%s" % (vol['id'], vol['name'])

        raw_msg = "Could not find volumes %s in expected list %s; fetched %s"
        self.fail(raw_msg % ([str_vol(v) for v in missing_vols],
                             [str_vol(v) for v in expected_list],
                             [str_vol(v) for v in fetched_list]))

    @classmethod
    def resource_setup(cls):
        super(VolumesListTestJSON, cls).resource_setup()

        existing_volumes = cls.volumes_client.list_volumes()['volumes']
        cls.volume_id_list = [vol['id'] for vol in existing_volumes]

        # Create 3 test volumes
        cls.volume_list = []
        cls.metadata = {'Type': 'work'}
        for _ in range(3):
            volume = cls.create_volume(metadata=cls.metadata)
            volume = cls.volumes_client.show_volume(volume['id'])['volume']
            cls.volume_list.append(volume)
            cls.volume_id_list.append(volume['id'])
        cls._remove_volatile_fields(cls.volume_list)

    def _list_by_param_value_and_assert(self, params, with_detail=False):
        """list or list_details with given params and validates result"""
        if with_detail:
            fetched_vol_list = \
                self.volumes_client.list_volumes(detail=True,
                                                 params=params)['volumes']
        else:
            fetched_vol_list = self.volumes_client.list_volumes(
                params=params)['volumes']

        # Validating params of fetched volumes
        if with_detail:
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

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('0b6ddd39-b948-471f-8038-4787978747c4')
    def test_volume_list(self):
        # Get a list of Volumes
        # Fetch all volumes
        fetched_list = self.volumes_client.list_volumes()['volumes']
        self._assert_volumes_in(fetched_list, self.volume_list,
                                fields=self.VOLUME_FIELDS)

    @decorators.idempotent_id('adcbb5a7-5ad8-4b61-bd10-5380e111a877')
    def test_volume_list_with_details(self):
        # Get a list of Volumes with details
        # Fetch all Volumes
        fetched_list = self.volumes_client.list_volumes(detail=True)['volumes']
        self._assert_volumes_in(fetched_list, self.volume_list)

    @decorators.idempotent_id('a28e8da4-0b56-472f-87a8-0f4d3f819c02')
    def test_volume_list_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name']}
        fetched_vol = self.volumes_client.list_volumes(
            params=params)['volumes']
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['name'], volume['name'])

    @decorators.idempotent_id('2de3a6d4-12aa-403b-a8f2-fdeb42a89623')
    def test_volume_list_details_by_name(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name']}
        fetched_vol = self.volumes_client.list_volumes(
            detail=True, params=params)['volumes']
        self.assertEqual(1, len(fetched_vol), str(fetched_vol))
        self.assertEqual(fetched_vol[0]['name'], volume['name'])

    @decorators.idempotent_id('39654e13-734c-4dab-95ce-7613bf8407ce')
    def test_volumes_list_by_status(self):
        params = {'status': 'available'}
        fetched_list = self.volumes_client.list_volumes(
            params=params)['volumes']
        self._list_by_param_value_and_assert(params)
        self._assert_volumes_in(fetched_list, self.volume_list,
                                fields=self.VOLUME_FIELDS)

    @decorators.idempotent_id('2943f712-71ec-482a-bf49-d5ca06216b9f')
    def test_volumes_list_details_by_status(self):
        params = {'status': 'available'}
        fetched_list = self.volumes_client.list_volumes(
            detail=True, params=params)['volumes']
        for volume in fetched_list:
            self.assertEqual('available', volume['status'])
        self._assert_volumes_in(fetched_list, self.volume_list)

    @decorators.idempotent_id('2016a942-3020-40d7-95ce-7613bf8407ce')
    def test_volumes_list_by_bootable(self):
        """Check out volumes.

        This test function is aim at check out whether all of the volumes
        in volume_list are not a bootable volume.
        """
        params = {'bootable': 'false'}
        fetched_list = self.volumes_client.list_volumes(
            params=params)['volumes']
        self._list_by_param_value_and_assert(params)
        self._assert_volumes_in(fetched_list, self.volume_list,
                                fields=self.VOLUME_FIELDS)

    @decorators.idempotent_id('2016a939-72ec-482a-bf49-d5ca06216b9f')
    def test_volumes_list_details_by_bootable(self):
        params = {'bootable': 'false'}
        fetched_list = self.volumes_client.list_volumes(
            detail=True, params=params)['volumes']
        for volume in fetched_list:
            self.assertEqual('false', volume['bootable'])
        self._assert_volumes_in(fetched_list, self.volume_list)

    @decorators.idempotent_id('c0cfa863-3020-40d7-b587-e35f597d5d87')
    def test_volumes_list_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        fetched_list = self.volumes_client.list_volumes(
            params=params)['volumes']
        self._list_by_param_value_and_assert(params)
        self._assert_volumes_in(fetched_list, self.volume_list,
                                fields=self.VOLUME_FIELDS)

    @decorators.idempotent_id('e1b80d13-94f0-4ba2-a40e-386af29f8db1')
    def test_volumes_list_details_by_availability_zone(self):
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        zone = volume['availability_zone']
        params = {'availability_zone': zone}
        fetched_list = self.volumes_client.list_volumes(
            detail=True, params=params)['volumes']
        for volume in fetched_list:
            self.assertEqual(zone, volume['availability_zone'])
        self._assert_volumes_in(fetched_list, self.volume_list)

    @decorators.idempotent_id('b5ebea1b-0603-40a0-bb41-15fcd0a53214')
    def test_volume_list_with_param_metadata(self):
        # Test to list volumes when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('1ca92d3c-4a8e-4b43-93f5-e4c7fb3b291d')
    def test_volume_list_with_detail_param_metadata(self):
        # Test to list volumes details when metadata param is given
        params = {'metadata': self.metadata}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @decorators.idempotent_id('777c87c1-2fc4-4883-8b8e-5c0b951d1ec8')
    def test_volume_list_param_display_name_and_status(self):
        # Test to list volume when display name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name'],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('856ab8ca-6009-4c37-b691-be1065528ad4')
    def test_volume_list_with_detail_param_display_name_and_status(self):
        # Test to list volume when name and status param is given
        volume = self.volume_list[data_utils.rand_int_id(0, 2)]
        params = {'name': volume['name'],
                  'status': 'available'}
        self._list_by_param_value_and_assert(params, with_detail=True)

    @decorators.idempotent_id('2a7064eb-b9c3-429b-b888-33928fc5edd3')
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
            fetched_volume = self.volumes_client.list_volumes(
                detail=True, params=params)['volumes']
            self.assertEqual(limit, len(fetched_volume),
                             "The count of volumes is %s, expected:%s " %
                             (len(fetched_volume), limit))
            self.assertEqual(status, fetched_volume[0]['status'])
            self.assertEqual(status, fetched_volume[1]['status'])
            val0 = fetched_volume[0][sort_key]
            val1 = fetched_volume[1][sort_key]
            if sort_dir == 'asc':
                self.assertLess(val0, val1,
                                "list is not in asc order with sort_key: %s."
                                " %s" % (sort_key, fetched_volume))
            elif sort_dir == 'desc':
                self.assertGreater(val0, val1,
                                   "list is not in desc order with sort_key: "
                                   "%s. %s" % (sort_key, fetched_volume))

        _list_details_with_multiple_params()
        _list_details_with_multiple_params(sort_dir='desc')

    def _test_pagination(self, resource, ids=None, limit=1, **kwargs):
        """Check list pagination functionality for a resource.

        This method requests the list of resources and follows pagination
        links.

        If an iterable is supplied in ids it will check that all ids are
        retrieved and that only those are listed, that we will get a next
        link for an empty page if the number of items is divisible by used
        limit (this is expected behavior).

        We can specify number of items per request using limit argument.
        """

        # Get list method for the type of resource from the client
        client = getattr(self, resource + '_client')
        method = getattr(client, 'list_' + resource)

        # Include limit in params for list request
        params = kwargs.pop('params', {})
        params['limit'] = limit

        # Store remaining items we are expecting from list
        if ids is not None:
            remaining = list(ids)
        else:
            remaining = None

        # Mark that the current iteration is not from a 'next' link
        next = None

        while True:
            # Get a list page
            response = method(params=params, **kwargs)

            # If we have to check ids
            if remaining is not None:
                # Confirm we receive expected number of elements
                num_expected = min(len(remaining), limit)
                self.assertEqual(num_expected, len(response[resource]),
                                 'Requested %(#expect)d but got %(#received)d '
                                 % {'#expect': num_expected,
                                    '#received': len(response[resource])})

                # For each received element
                for element in response[resource]:
                    element_id = element['id']
                    # Check it's one of expected ids
                    self.assertIn(element_id,
                                  ids,
                                  'Id %(id)s is not in expected ids %(ids)s' %
                                  {'id': element_id, 'ids': ids})
                    # If not in remaining, we have received it twice
                    self.assertIn(element_id,
                                  remaining,
                                  'Id %s was received twice' % element_id)
                    # We no longer expect it
                    remaining.remove(element_id)

            # If the current iteration is from a 'next' link, check that the
            # absolute url is the same as the one used for this request
            if next:
                self.assertEqual(next, response.response['content-location'])

            # Get next from response
            next = None
            for link in response.get(resource + '_links', ()):
                if link['rel'] == 'next':
                    next = link['href']
                    break

            # Check if we have next and we shouldn't or the other way around
            if remaining is not None:
                if remaining or (num_expected and len(ids) % limit == 0):
                    self.assertIsNotNone(next, 'Missing link to next page')
                else:
                    self.assertIsNone(next, 'Unexpected link to next page')

            # If we can follow to the next page, get params from url to make
            # request in the form of a relative URL
            if next:
                params = parse.urlparse(next).query

            # If cannot follow make sure it's because we have finished
            else:
                self.assertEmpty(remaining or [],
                                 'No more pages reported, but still '
                                 'missing ids %s' % remaining)
                break

    @decorators.idempotent_id('e9138a2c-f67b-4796-8efa-635c196d01de')
    def test_volume_list_details_pagination(self):
        self._test_pagination('volumes', ids=self.volume_id_list, detail=True)

    @decorators.idempotent_id('af55e775-8e4b-4feb-8719-215c43b0238c')
    def test_volume_list_pagination(self):
        self._test_pagination('volumes', ids=self.volume_id_list, detail=False)

    @decorators.idempotent_id('46eff077-100b-427f-914e-3db2abcdb7e2')
    def test_volume_list_with_detail_param_marker(self):
        # Choosing a random volume from a list of volumes for 'marker'
        # parameter
        marker = random.choice(self.volume_id_list)

        # Though Cinder volumes are returned sorted by ID by default
        # this is implicit. Let make this explicit in case Cinder
        # folks change their minds.
        params = {'marker': marker, 'sort': 'id:asc'}

        # Running volume list using marker parameter
        vol_with_marker = self.volumes_client.list_volumes(
            detail=True, params=params)['volumes']

        expected_volumes_id = {
            id for id in self.volume_id_list if id > marker
        }

        self.assertEqual(
            expected_volumes_id, {v['id'] for v in vol_with_marker}
        )
