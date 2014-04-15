# Copyright 2014 OpenStack Foundation
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

from tempest.api.identity import base
from tempest import test


class CertificatesV3TestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    def _verify_response(self, expected, actual):
        missing_tags = [t for t in expected if t not in actual]
        self.assertEqual(0, len(missing_tags),
                         "Failed to fetch expected tag"
                         "in the certificate: %s" % ','.join(missing_tags))

    @test.attr(type='smoke')
    def test_get_ca_certificate(self):
        # Verify ca certificate chain
        expected_tags = ['BEGIN CERTIFICATE', 'END CERTIFICATE']
        resp, certificate = self.client.get_ca_certificate()
        self.assertEqual(200, resp.status)
        self._verify_response(expected_tags, certificate)

    @test.attr(type='smoke')
    def test_get_certificates(self):
        # Verify signing certificates
        expected_tags = ['Certificate', 'BEGIN CERTIFICATE', 'END CERTIFICATE']
        resp, certificates = self.client.get_certificates()
        self.assertEqual(200, resp.status)
        self._verify_response(expected_tags, certificates)
