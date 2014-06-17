# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest import test


class CertificatesV3Test(base.BaseComputeTest):

    _api_version = 3

    @test.attr(type='gate')
    def test_create_root_certificate(self):
        # create certificates
        resp, body = self.certificates_client.create_certificate()
        self.assertIn('data', body)
        self.assertIn('private_key', body)

    @test.attr(type='gate')
    def test_get_root_certificate(self):
        # get the root certificate
        resp, body = self.certificates_client.get_certificate('root')
        self.assertEqual(200, resp.status)
        self.assertIn('data', body)
        self.assertIn('private_key', body)


class CertificatesV2TestJSON(CertificatesV3Test):
    _api_version = 2


class CertificatesV2TestXML(CertificatesV2TestJSON):
    _interface = 'xml'
