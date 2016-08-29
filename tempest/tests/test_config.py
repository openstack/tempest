# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import testtools

from tempest import config
from tempest.lib import exceptions
from tempest.tests import base
from tempest.tests import fake_config


class TestServiceClientConfig(base.TestCase):

    expected_common_params = set(['disable_ssl_certificate_validation',
                                  'ca_certs', 'trace_requests'])
    expected_extra_params = set(['service', 'endpoint_type', 'region',
                                 'build_timeout', 'build_interval'])

    def setUp(self):
        super(TestServiceClientConfig, self).setUp()
        self.useFixture(fake_config.ServiceClientsConfigFixture())
        self.patchobject(config, 'CONF',
                         fake_config.ServiceClientsFakePrivate())
        self.CONF = config.CONF

    def test_service_client_config_no_service(self):
        params = config.service_client_config()
        for param_name in self.expected_common_params:
            self.assertIn(param_name, params)
        for param_name in self.expected_extra_params:
            self.assertNotIn(param_name, params)
        self.assertEqual(
            self.CONF.identity.disable_ssl_certificate_validation,
            params['disable_ssl_certificate_validation'])
        self.assertEqual(self.CONF.identity.ca_certificates_file,
                         params['ca_certs'])
        self.assertEqual(self.CONF.debug.trace_requests,
                         params['trace_requests'])

    def test_service_client_config_service_all(self):
        params = config.service_client_config(
            service_client_name='fake-service1')
        for param_name in self.expected_common_params:
            self.assertIn(param_name, params)
        for param_name in self.expected_extra_params:
            self.assertIn(param_name, params)
        self.assertEqual(self.CONF.fake_service1.catalog_type,
                         params['service'])
        self.assertEqual(self.CONF.fake_service1.endpoint_type,
                         params['endpoint_type'])
        self.assertEqual(self.CONF.fake_service1.region, params['region'])
        self.assertEqual(self.CONF.fake_service1.build_timeout,
                         params['build_timeout'])
        self.assertEqual(self.CONF.fake_service1.build_interval,
                         params['build_interval'])

    def test_service_client_config_service_minimal(self):
        params = config.service_client_config(
            service_client_name='fake-service2')
        for param_name in self.expected_common_params:
            self.assertIn(param_name, params)
        for param_name in self.expected_extra_params:
            self.assertIn(param_name, params)
        self.assertEqual(self.CONF.fake_service2.catalog_type,
                         params['service'])
        self.assertEqual(self.CONF.fake_service2.endpoint_type,
                         params['endpoint_type'])
        self.assertEqual(self.CONF.identity.region, params['region'])
        self.assertEqual(self.CONF.compute.build_timeout,
                         params['build_timeout'])
        self.assertEqual(self.CONF.compute.build_interval,
                         params['build_interval'])

    def test_service_client_config_service_unknown(self):
        unknown_service = 'unknown_service'
        with testtools.ExpectedException(exceptions.UnknownServiceClient,
                                         '.*' + unknown_service + '.*'):
            config.service_client_config(service_client_name=unknown_service)
