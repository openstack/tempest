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

from tempest.services.compute.json import certificates_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestCertificatesClient(base.TestCase):

    FAKE_CERTIFICATE = {
        "certificate": {
            "data": "-----BEGIN----MIICyzCCAjSgAwI----END CERTIFICATE-----\n",
            "private_key": None
        }
    }

    def setUp(self):
        super(TestCertificatesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = certificates_client.CertificatesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_show_certificate(self, bytes_body=False):
        serialized_body = json.dumps(self.FAKE_CERTIFICATE)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_certificate("fake-id")
        self.assertEqual(self.FAKE_CERTIFICATE, resp)

    def test_show_certificate_with_str_body(self):
        self._test_show_certificate()

    def test_show_certificate_with_bytes_body(self):
        self._test_show_certificate(bytes_body=True)

    def _test_create_certificate(self, bytes_body=False):
        cert = copy.deepcopy(self.FAKE_CERTIFICATE)
        cert['certificate']['private_key'] = "my_private_key"
        serialized_body = json.dumps(cert)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.post',
            return_value=mocked_resp))
        resp = self.client.create_certificate()
        self.assertEqual(cert, resp)

    def test_create_certificate_with_str_body(self):
        self._test_create_certificate()

    def test_create_certificate_with_bytes_body(self):
        self._test_create_certificate(bytes_body=True)
