# Copyright 2015 NEC Corporation.  All rights reserved.
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

import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import aggregates_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestAggregatesClient(base.TestCase):

    def setUp(self):
        super(TestAggregatesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = aggregates_client.AggregatesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_aggregates(self, bytes_body=False):
        body = '{"aggregates": []}'
        if bytes_body:
            body = body.encode('utf-8')
        expected = []
        response = (httplib2.Response({'status': 200}), body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=response))
        self.assertEqual(expected, self.client.list_aggregates())

    def test_list_aggregates_with_str_body(self):
        self._test_list_aggregates()

    def test_list_aggregates_with_bytes_body(self):
        self._test_list_aggregates(bytes_body=True)

    def _test_show_aggregate(self, bytes_body=False):
        expected = {"name": "hoge",
                    "availability_zone": None,
                    "deleted": False,
                    "created_at":
                    "2015-07-16T03:07:32.000000",
                    "updated_at": None,
                    "hosts": [],
                    "deleted_at": None,
                    "id": 1,
                    "metadata": {}}
        serialized_body = json.dumps({"aggregate": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_aggregate(1)
        self.assertEqual(expected, resp)

    def test_show_aggregate_with_str_body(self):
        self._test_show_aggregate()

    def test_show_aggregate_with_bytes_body(self):
        self._test_show_aggregate(bytes_body=True)

    def _test_create_aggregate(self, bytes_body=False):
        expected = {"name": u'\xf4',
                    "availability_zone": None,
                    "deleted": False,
                    "created_at": "2015-07-21T04:11:18.000000",
                    "updated_at": None,
                    "deleted_at": None,
                    "id": 1}
        serialized_body = json.dumps({"aggregate": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.post',
            return_value=mocked_resp))
        resp = self.client.create_aggregate(name='hoge')
        self.assertEqual(expected, resp)

    def test_create_aggregate_with_str_body(self):
        self._test_create_aggregate()

    def test_create_aggregate_with_bytes_body(self):
        self._test_create_aggregate(bytes_body=True)

    def test_delete_aggregate(self):
        expected = {}
        mocked_resp = (httplib2.Response({'status': 200}), None)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.delete',
            return_value=mocked_resp))
        resp = self.client.delete_aggregate("1")
        self.assertEqual(expected, resp)

    def _test_update_aggregate(self, bytes_body=False):
        expected = {"name": u'\xe9',
                    "availability_zone": None,
                    "deleted": False,
                    "created_at": "2015-07-16T03:07:32.000000",
                    "updated_at": "2015-07-23T05:16:29.000000",
                    "hosts": [],
                    "deleted_at": None,
                    "id": 1,
                    "metadata": {}}
        serialized_body = json.dumps({"aggregate": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.put',
            return_value=mocked_resp))
        resp = self.client.update_aggregate(1)
        self.assertEqual(expected, resp)

    def test_update_aggregate_with_str_body(self):
        self._test_update_aggregate()

    def test_update_aggregate_with_bytes_body(self):
        self._test_update_aggregate(bytes_body=True)
