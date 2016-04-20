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

import random
from six.moves.urllib import parse

from tempest.api.volume import base
from tempest.lib import decorators
from tempest import test


class VolumesV2ListTestJSON(base.BaseVolumeTest):
    """volumes v2 specific tests.

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
            volume = cls.client.show_volume(volume['id'])['volume']
            cls.volume_list.append(volume)
            cls.volume_id_list.append(volume['id'])

    @classmethod
    def resource_cleanup(cls):
        # Delete the created volumes
        for volid in cls.volume_id_list:
            cls.client.delete_volume(volid)
            cls.client.wait_for_resource_deletion(volid)
        super(VolumesV2ListTestJSON, cls).resource_cleanup()

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
            fetched_volume = self.client.list_volumes(
                detail=True, params=params)['volumes']
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
                self.assertListEqual([], remaining or [],
                                     'No more pages reported, but still '
                                     'missing ids %s' % remaining)
                break

    @test.idempotent_id('e9138a2c-f67b-4796-8efa-635c196d01de')
    def test_volume_list_details_pagination(self):
        self._test_pagination('volumes', ids=self.volume_id_list, detail=True)

    @test.idempotent_id('af55e775-8e4b-4feb-8719-215c43b0238c')
    def test_volume_list_pagination(self):
        self._test_pagination('volumes', ids=self.volume_id_list, detail=False)

    @test.idempotent_id('46eff077-100b-427f-914e-3db2abcdb7e2')
    @decorators.skip_because(bug='1572765')
    def test_volume_list_with_detail_param_marker(self):
        # Choosing a random volume from a list of volumes for 'marker'
        # parameter
        random_volume = random.choice(self.volume_id_list)

        params = {'marker': random_volume}

        # Running volume list using marker parameter
        vol_with_marker = self.client.list_volumes(detail=True,
                                                   params=params)['volumes']

        # Fetching the index of the random volume from volume_id_list
        index_marker = self.volume_id_list.index(random_volume)

        # The expected list with marker parameter
        verify_volume_list = self.volume_id_list[:index_marker]

        failed_msg = "Failed to list volume details by marker"

        # Validating the expected list is the same like the observed list
        self.assertEqual(verify_volume_list,
                         map(lambda x: x['id'],
                             vol_with_marker[::-1]), failed_msg)
