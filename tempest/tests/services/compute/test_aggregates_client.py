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
