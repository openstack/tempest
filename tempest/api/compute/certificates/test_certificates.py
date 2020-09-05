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
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class CertificatesV2TestJSON(base.BaseV2ComputeTest):
    """Test Certificates API"""

    @classmethod
    def skip_checks(cls):
        super(CertificatesV2TestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.nova_cert:
            raise cls.skipException("Nova cert is not available")

    @decorators.idempotent_id('c070a441-b08e-447e-a733-905909535b1b')
    def test_create_root_certificate(self):
        """Test creating root certificate"""
        self.certificates_client.create_certificate()

    @decorators.idempotent_id('3ac273d0-92d2-4632-bdfc-afbc21d4606c')
    def test_get_root_certificate(self):
        """Test getting root certificate details"""
        self.certificates_client.show_certificate('root')
