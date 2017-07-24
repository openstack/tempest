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

from tempest.lib.common import http
from tempest.tests import base


class TestClosingHttp(base.TestCase):
    def setUp(self):
        super(TestClosingHttp, self).setUp()
        self.cert_none = "CERT_NONE"
        self.cert_location = "/etc/ssl/certs/ca-certificates.crt"

    def test_constructor_invalid_ca_certs_and_timeout(self):
        connection = http.ClosingHttp(
            disable_ssl_certificate_validation=False,
            ca_certs=None,
            timeout=None)
        for attr in ('cert_reqs', 'ca_certs', 'timeout'):
            self.assertNotIn(attr, connection.connection_pool_kw)

    def test_constructor_valid_ca_certs(self):
        cert_required = 'CERT_REQUIRED'
        connection = http.ClosingHttp(
            disable_ssl_certificate_validation=False,
            ca_certs=self.cert_location,
            timeout=None)
        self.assertEqual(cert_required,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertEqual(self.cert_location,
                         connection.connection_pool_kw['ca_certs'])
        self.assertNotIn('timeout',
                         connection.connection_pool_kw)

    def test_constructor_ssl_cert_validation_disabled(self):
        connection = http.ClosingHttp(
            disable_ssl_certificate_validation=True,
            ca_certs=None,
            timeout=30)
        self.assertEqual(self.cert_none,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertEqual(30,
                         connection.connection_pool_kw['timeout'])
        self.assertNotIn('ca_certs',
                         connection.connection_pool_kw)

    def test_constructor_ssl_cert_validation_disabled_and_ca_certs(self):
        connection = http.ClosingHttp(
            disable_ssl_certificate_validation=True,
            ca_certs=self.cert_location,
            timeout=None)
        self.assertNotIn('timeout',
                         connection.connection_pool_kw)
        self.assertEqual(self.cert_none,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertNotIn('ca_certs',
                         connection.connection_pool_kw)
