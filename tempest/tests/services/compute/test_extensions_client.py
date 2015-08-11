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

from tempest.services.compute.json import extensions_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestExtensionsClient(base.TestCase):

    def setUp(self):
        super(TestExtensionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = extensions_client.ExtensionsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_extensions(self, bytes_body=False):
        body = '{"extensions": []}'
        if bytes_body:
            body = body.encode('utf-8')
        expected = []
        response = (httplib2.Response({'status': 200}), body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=response))
        self.assertEqual(expected, self.client.list_extensions())

    def test_list_extensions_with_str_body(self):
        self._test_list_extensions()

    def test_list_extensions_with_bytes_body(self):
        self._test_list_extensions(bytes_body=True)

    def _test_show_extension(self, bytes_body=False):
        expected = {
            "updated": "2011-06-09T00:00:00Z",
            "name": "Multinic",
            "links": [],
            "namespace":
            "http://docs.openstack.org/compute/ext/multinic/api/v1.1",
            "alias": "NMN",
            "description": u'\u2740(*\xb4\u25e1`*)\u2740'
        }
        serialized_body = json.dumps({"extension": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_extension("NMN")
        self.assertEqual(expected, resp)

    def test_show_extension_with_str_body(self):
        self._test_show_extension()

    def test_show_extension_with_bytes_body(self):
        self._test_show_extension(bytes_body=True)
