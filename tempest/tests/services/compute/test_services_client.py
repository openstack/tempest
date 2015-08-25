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

import copy
import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import services_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestServicesClient(base.TestCase):

    FAKE_SERVICES = [{
        "status": "enabled",
        "binary": "nova-conductor",
        "zone": "internal",
        "state": "up",
        "updated_at": "2015-08-19T06:50:55.000000",
        "host": "controller",
        "disabled_reason": None,
        "id": 1
        }]

    FAKE_SERVICE = {
        "status": "enabled",
        "binary": "nova-conductor",
        "host": "controller"
        }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_services(self, bytes_body=False):
        expected = {"services": self.FAKE_SERVICES}
        serialized_body = json.dumps(expected)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.list_services()
        self.assertEqual(expected, resp)

    def test_list_services_with_str_body(self):
        self._test_list_services()

    def test_list_services_with_bytes_body(self):
        self._test_list_services(bytes_body=True)

    def _test_enable_service(self, bytes_body=False):
        expected = {"service": self.FAKE_SERVICE}
        serialized_body = json.dumps(expected)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.put',
            return_value=mocked_resp))
        resp = self.client.enable_service("nova-conductor", "controller")
        self.assertEqual(expected, resp)

    def test_enable_service_with_str_body(self):
        self._test_enable_service()

    def test_enable_service_with_bytes_body(self):
        self._test_enable_service(bytes_body=True)

    def _test_disable_service(self, bytes_body=False):
        fake_service = copy.deepcopy(self.FAKE_SERVICE)
        fake_service["status"] = "disable"
        expected = {"service": self.FAKE_SERVICE}
        serialized_body = json.dumps(expected)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.put',
            return_value=mocked_resp))
        resp = self.client.disable_service("nova-conductor", "controller")
        self.assertEqual(expected, resp)

    def test_disable_service_with_str_body(self):
        self._test_enable_service()

    def test_disable_service_with_bytes_body(self):
        self._test_enable_service(bytes_body=True)
