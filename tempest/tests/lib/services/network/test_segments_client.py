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

import copy

from tempest.lib.services.network import segments_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSegmentsClient(base.BaseServiceTest):

    FAKE_SEGMENT_ID = '83a59912-a473-11e9-a012-af494c35c9c2'
    FAKE_NETWORK_ID = '913ab0e4-a473-11e9-84a3-af1c16fc05de'

    FAKE_SEGMENT_REQUEST = {
        'segment': {
            'network_id': FAKE_NETWORK_ID,
            'segmentation_id': 2000,
            'network_type': 'vlan',
            'physical_network': 'segment-1'
        }
    }

    FAKE_SEGMENT_RESPONSE = {
        'segment': {
            'name': 'foo',
            'network_id': FAKE_NETWORK_ID,
            'segmentation_id': 2000,
            'network_type': 'vlan',
            'physical_network': 'segment-1',
            'revision_number': 1,
            'id': FAKE_SEGMENT_ID,
            'created_at': '2019-07-12T09:13:56Z',
            'updated_at': '2019-07-12T09:13:56Z',
            'description': 'bar'
        }
    }

    FAKE_SEGMENTS = {
        'segments': [
            FAKE_SEGMENT_RESPONSE['segment']
        ]
    }

    def setUp(self):
        super(TestSegmentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.segments_client = segments_client.SegmentsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_segment(self, bytes_body=False):
        self.check_service_client_function(
            self.segments_client.create_segment,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SEGMENT_RESPONSE,
            bytes_body,
            201,
            **self.FAKE_SEGMENT_REQUEST['segment']
        )

    def _test_list_segments(self, bytes_body=False):
        self.check_service_client_function(
            self.segments_client.list_segments,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SEGMENTS,
            bytes_body,
            200
        )

    def _test_show_segment(self, bytes_body=False):
        self.check_service_client_function(
            self.segments_client.show_segment,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SEGMENT_RESPONSE,
            bytes_body,
            200,
            segment_id=self.FAKE_SEGMENT_ID
        )

    def _test_update_segment(self, bytes_body=False):
        update_kwargs = {
            'name': 'notfoo'
        }

        resp_body = {
            'segment': copy.deepcopy(self.FAKE_SEGMENT_RESPONSE['segment'])
        }
        resp_body['segment'].update(update_kwargs)

        self.check_service_client_function(
            self.segments_client.update_segment,
            'tempest.lib.common.rest_client.RestClient.put',
            resp_body,
            bytes_body,
            200,
            segment_id=self.FAKE_SEGMENT_ID,
            **update_kwargs
        )

    def test_create_segment_with_str_body(self):
        self._test_create_segment()

    def test_create_segment_with_bytes_body(self):
        self._test_create_segment(bytes_body=True)

    def test_update_segment_with_str_body(self):
        self._test_update_segment()

    def test_update_segment_with_bytes_body(self):
        self._test_update_segment(bytes_body=True)

    def test_show_segment_with_str_body(self):
        self._test_show_segment()

    def test_show_segment_with_bytes_body(self):
        self._test_show_segment(bytes_body=True)

    def test_delete_segment(self):
        self.check_service_client_function(
            self.segments_client.delete_segment,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            segment_id=self.FAKE_SEGMENT_ID)

    def test_list_segment_with_str_body(self):
        self._test_list_segments()

    def test_list_segment_with_bytes_body(self):
        self._test_list_segments(bytes_body=True)
