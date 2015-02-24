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


class CertificatesV2TestJSON(base.BaseComputeTest):

    _api_version = 2

    @test.attr(type='gate')
    @test.idempotent_id('c070a441-b08e-447e-a733-905909535b1b')
    def test_create_root_certificate(self):
        # create certificates
        body = self.certificates_client.create_certificate()
        self.assertIn('data', body)
        self.assertIn('private_key', body)

    @test.attr(type='gate')
    @test.idempotent_id('3ac273d0-92d2-4632-bdfc-afbc21d4606c')
    def test_get_root_certificate(self):
        # get the root certificate
        body = self.certificates_client.get_certificate('root')
        self.assertIn('data', body)
        self.assertIn('private_key', body)
