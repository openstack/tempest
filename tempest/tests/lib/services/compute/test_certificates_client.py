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

from tempest.lib.services.compute import certificates_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestCertificatesClient(base.BaseServiceTest):

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
        self.check_service_client_function(
            self.client.show_certificate,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CERTIFICATE,
            bytes_body,
            certificate_id="fake-id")

    def test_show_certificate_with_str_body(self):
        self._test_show_certificate()

    def test_show_certificate_with_bytes_body(self):
        self._test_show_certificate(bytes_body=True)

    def _test_create_certificate(self, bytes_body=False):
        cert = copy.deepcopy(self.FAKE_CERTIFICATE)
        cert['certificate']['private_key'] = "my_private_key"
        self.check_service_client_function(
            self.client.create_certificate,
            'tempest.lib.common.rest_client.RestClient.post',
            cert,
            bytes_body)

    def test_create_certificate_with_str_body(self):
        self._test_create_certificate()

    def test_create_certificate_with_bytes_body(self):
        self._test_create_certificate(bytes_body=True)
