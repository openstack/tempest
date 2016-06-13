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

import fixtures
import testtools

from tempest.lib import auth
from tempest.lib import exceptions
from tempest import service_clients
from tempest.tests import base
from tempest.tests.lib import fake_credentials


class TestServiceClients(base.TestCase):

    def setUp(self):
        super(TestServiceClients, self).setUp()
        self.useFixture(fixtures.MockPatch(
            'tempest.service_clients.tempest_modules',
            return_value=set(['fake_service1', 'fake_service2'])))

    def test___init___creds_v2_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV2Credentials()
        uri = 'fake_uri'
        _manager = service_clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV2AuthProvider)

    def test___init___creds_v3_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV3Credentials()
        uri = 'fake_uri'
        _manager = service_clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV3AuthProvider)

    def test___init___base_creds_uri(self):
        creds = fake_credentials.FakeCredentials()
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            service_clients.ServiceClients(creds, identity_uri=uri)

    def test___init___invalid_creds_uri(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        delattr(creds, 'username')
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            service_clients.ServiceClients(creds, identity_uri=uri)

    def test___init___creds_uri_none(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        msg = ("Invalid Credentials\nDetails: ServiceClients requires a "
               "non-empty")
        with testtools.ExpectedException(exceptions.InvalidCredentials,
                                         value_re=msg):
            service_clients.ServiceClients(creds, None)

    def test___init___creds_uri_params(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        expeted_params = {'fake_param1': 'fake_value1',
                          'fake_param2': 'fake_value2'}
        params = {'fake_service1': expeted_params}
        uri = 'fake_uri'
        _manager = service_clients.ServiceClients(creds, identity_uri=uri,
                                                  client_parameters=params)
        self.assertIn('fake_service1', _manager.parameters.keys())
        for _key in expeted_params.keys():
            self.assertIn(_key, _manager.parameters['fake_service1'].keys())
            self.assertEqual(expeted_params[_key],
                             _manager.parameters['fake_service1'].get(_key))

    def test___init___creds_uri_params_unknown_services(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        fake_params = {'fake_param1': 'fake_value1'}
        params = {'unknown_service1': fake_params,
                  'unknown_service2': fake_params}
        uri = 'fake_uri'
        msg = "(?=.*{0})(?=.*{1})".format(*list(params.keys()))
        with testtools.ExpectedException(
                exceptions.UnknownServiceClient, value_re=msg):
            service_clients.ServiceClients(creds, identity_uri=uri,
                                           client_parameters=params)

    def _get_manager(self, init_region='fake_region'):
        # Get a manager to invoke _setup_parameters on
        creds = fake_credentials.FakeKeystoneV2Credentials()
        return service_clients.ServiceClients(creds, identity_uri='fake_uri',
                                              region=init_region)

    def test__setup_parameters_none_no_region(self):
        kwargs = {}
        _manager = self._get_manager(init_region=None)
        _params = _manager._setup_parameters(kwargs)
        self.assertNotIn('region', _params)

    def test__setup_parameters_none(self):
        kwargs = {}
        _manager = self._get_manager()
        _params = _manager._setup_parameters(kwargs)
        self.assertIn('region', _params)
        self.assertEqual('fake_region', _params['region'])

    def test__setup_parameters_all(self):
        expected_params = {'region': 'fake_region1',
                           'catalog_type': 'fake_service2_mod',
                           'fake_param1': 'fake_value1',
                           'fake_param2': 'fake_value2'}
        _manager = self._get_manager()
        _params = _manager._setup_parameters(expected_params)
        for _key in _params.keys():
            self.assertEqual(expected_params[_key],
                             _params[_key])
