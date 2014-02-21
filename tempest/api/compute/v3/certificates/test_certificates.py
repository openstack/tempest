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
from tempest.test import attr


class CertificatesV3Test(base.BaseV3ComputeTest):

    @attr(type='gate')
    def test_create_and_get_root_certificate(self):
        # create certificates
        resp, create_body = self.certificates_client.create_certificate()
        self.assertEqual(201, resp.status)
        self.assertIn('data', create_body)
        self.assertIn('private_key', create_body)
        # get the root certificate
        resp, body = self.certificates_client.get_certificate('root')
        self.assertEqual(200, resp.status)
        self.assertIn('data', body)
        self.assertIn('private_key', body)
