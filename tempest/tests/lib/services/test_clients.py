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

import types
from unittest import mock

import fixtures
import testtools

from tempest.lib import auth
from tempest.lib import exceptions
from tempest.lib.services import clients
from tempest.tests import base
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_credentials


has_attribute = testtools.matchers.MatchesPredicateWithParams(
    lambda x, y: hasattr(x, y), '{0} does not have an attribute {1}')


class TestClientsFactory(base.TestCase):

    def setUp(self):
        super(TestClientsFactory, self).setUp()
        self.classes = []

    def _setup_fake_module(self, class_names=None, extra_dict=None):
        class_names = class_names or []
        fake_module = types.ModuleType('fake_service_client')
        _dict = {}
        # Add fake classes to the fake module
        for name in class_names:
            _dict[name] = type(name, (object,), {})
            # Store it for assertions
            self.classes.append(_dict[name])
        if extra_dict:
            _dict[extra_dict] = extra_dict
        fake_module.__dict__.update(_dict)
        fixture_importlib = self.useFixture(fixtures.MockPatch(
            'importlib.import_module', return_value=fake_module))
        return fixture_importlib.mock

    def test___init___one_class(self):
        fake_partial = 'fake_partial'
        partial_mock = self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory._get_partial_class',
            return_value=fake_partial)).mock
        class_names = ['FakeServiceClient1']
        mock_importlib = self._setup_fake_module(class_names=class_names)
        auth_provider = fake_auth_provider.FakeAuthProvider()
        params = {'k1': 'v1', 'k2': 'v2'}
        factory = clients.ClientsFactory('fake_path', class_names,
                                         auth_provider, **params)
        # Assert module has been imported
        mock_importlib.assert_called_once_with('fake_path')
        # All attributes have been created
        for client in class_names:
            self.assertThat(factory, has_attribute(client))
        # Partial have been invoked correctly
        partial_mock.assert_called_once_with(
            self.classes[0], auth_provider, params)
        # Get the clients
        for name in class_names:
            self.assertEqual(fake_partial, getattr(factory, name))

    def test___init___two_classes(self):
        fake_partial = 'fake_partial'
        partial_mock = self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory._get_partial_class',
            return_value=fake_partial)).mock
        class_names = ['FakeServiceClient1', 'FakeServiceClient2']
        mock_importlib = self._setup_fake_module(class_names=class_names)
        auth_provider = fake_auth_provider.FakeAuthProvider()
        params = {'k1': 'v1', 'k2': 'v2'}
        factory = clients.ClientsFactory('fake_path', class_names,
                                         auth_provider, **params)
        # Assert module has been imported
        mock_importlib.assert_called_once_with('fake_path')
        # All attributes have been created
        for client in class_names:
            self.assertThat(factory, has_attribute(client))
        # Partial have been invoked the right number of times
        partial_mock.call_count = len(class_names)
        # Get the clients
        for name in class_names:
            self.assertEqual(fake_partial, getattr(factory, name))

    def test___init___no_module(self):
        auth_provider = fake_auth_provider.FakeAuthProvider()
        class_names = ['FakeServiceClient1', 'FakeServiceClient2']
        self.assertRaises(ImportError, clients.ClientsFactory,
                          'fake_module', class_names, auth_provider)

    def test___init___not_a_class(self):
        class_names = ['FakeServiceClient1', 'FakeServiceClient2']
        extended_class_names = class_names + ['not_really_a_class']
        self._setup_fake_module(
            class_names=class_names, extra_dict='not_really_a_class')
        auth_provider = fake_auth_provider.FakeAuthProvider()
        expected_msg = '.*not_really_a_class.*str.*'
        with testtools.ExpectedException(TypeError, expected_msg):
            clients.ClientsFactory('fake_module', extended_class_names,
                                   auth_provider)

    def test___init___class_not_found(self):
        class_names = ['FakeServiceClient1', 'FakeServiceClient2']
        extended_class_names = class_names + ['not_really_a_class']
        self._setup_fake_module(class_names=class_names)
        auth_provider = fake_auth_provider.FakeAuthProvider()
        expected_msg = '.*not_really_a_class.*fake_service_client.*'
        with testtools.ExpectedException(AttributeError, expected_msg):
            clients.ClientsFactory('fake_module', extended_class_names,
                                   auth_provider)

    def test__get_partial_class_no_later_kwargs(self):
        expected_fake_client = 'not_really_a_client'
        self._setup_fake_module(class_names=[])
        auth_provider = fake_auth_provider.FakeAuthProvider()
        params = {'k1': 'v1', 'k2': 'v2'}
        factory = clients.ClientsFactory(
            'fake_path', [], auth_provider, **params)
        klass_mock = mock.Mock(return_value=expected_fake_client)
        partial = factory._get_partial_class(klass_mock, auth_provider, params)
        # Class has not be initialised yet
        klass_mock.assert_not_called()
        # Use partial and assert on parameters
        client = partial()
        self.assertEqual(expected_fake_client, client)
        klass_mock.assert_called_once_with(auth_provider=auth_provider,
                                           **params)

    def test__get_partial_class_later_kwargs(self):
        expected_fake_client = 'not_really_a_client'
        self._setup_fake_module(class_names=[])
        auth_provider = fake_auth_provider.FakeAuthProvider()
        params = {'k1': 'v1', 'k2': 'v2'}
        later_params = {'k2': 'v4', 'k3': 'v3'}
        factory = clients.ClientsFactory(
            'fake_path', [], auth_provider, **params)
        klass_mock = mock.Mock(return_value=expected_fake_client)
        partial = factory._get_partial_class(klass_mock, auth_provider, params)
        # Class has not be initialised yet
        klass_mock.assert_not_called()
        # Use partial and assert on parameters
        client = partial(**later_params)
        params.update(later_params)
        self.assertEqual(expected_fake_client, client)
        klass_mock.assert_called_once_with(auth_provider=auth_provider,
                                           **params)

    def test__get_partial_class_with_alias(self):
        expected_fake_client = 'not_really_a_client'
        client_alias = 'fake_client'
        self._setup_fake_module(class_names=[])
        auth_provider = fake_auth_provider.FakeAuthProvider()
        params = {'k1': 'v1', 'k2': 'v2'}
        later_params = {'k2': 'v4', 'k3': 'v3'}
        factory = clients.ClientsFactory(
            'fake_path', [], auth_provider, **params)
        klass_mock = mock.Mock(return_value=expected_fake_client)
        partial = factory._get_partial_class(klass_mock, auth_provider, params)
        # Class has not be initialised yet
        klass_mock.assert_not_called()
        # Use partial and assert on parameters
        client = partial(alias=client_alias, **later_params)
        params.update(later_params)
        self.assertEqual(expected_fake_client, client)
        klass_mock.assert_called_once_with(auth_provider=auth_provider,
                                           **params)
        self.assertThat(factory, has_attribute(client_alias))
        self.assertEqual(expected_fake_client, getattr(factory, client_alias))


class TestServiceClients(base.TestCase):

    def setUp(self):
        super(TestServiceClients, self).setUp()
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.tempest_modules',
            return_value=set(['fake_service1'])))

    def test___init___creds_v2_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV2Credentials()
        uri = 'fake_uri'
        _manager = clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV2AuthProvider)

    def test___init___creds_v3_uri(self):
        # Verify that no API request is made, since no mock
        # is required to run the test successfully
        creds = fake_credentials.FakeKeystoneV3Credentials()
        uri = 'fake_uri'
        _manager = clients.ServiceClients(creds, identity_uri=uri)
        self.assertIsInstance(_manager.auth_provider,
                              auth.KeystoneV3AuthProvider)

    def test___init___base_creds_uri(self):
        creds = fake_credentials.FakeCredentials()
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            clients.ServiceClients(creds, identity_uri=uri)

    def test___init___invalid_creds_uri(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        delattr(creds, 'username')
        uri = 'fake_uri'
        with testtools.ExpectedException(exceptions.InvalidCredentials):
            clients.ServiceClients(creds, identity_uri=uri)

    def test___init___creds_uri_none(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        msg = ("Invalid Credentials\nDetails: ServiceClients requires a "
               "non-empty")
        with testtools.ExpectedException(exceptions.InvalidCredentials,
                                         value_re=msg):
            clients.ServiceClients(creds, None)

    def test___init___creds_uri_params(self):
        creds = fake_credentials.FakeKeystoneV2Credentials()
        expeted_params = {'fake_param1': 'fake_value1',
                          'fake_param2': 'fake_value2'}
        params = {'fake_service1': expeted_params}
        uri = 'fake_uri'
        _manager = clients.ServiceClients(creds, identity_uri=uri,
                                          client_parameters=params)
        self.assertIn('fake_service1', _manager.parameters)
        for _key in expeted_params:
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
            clients.ServiceClients(creds, identity_uri=uri,
                                   client_parameters=params)

    def test___init___plugin_service_clients_cannot_load(self):
        creds = fake_credentials.FakeKeystoneV3Credentials()
        uri = 'fake_uri'
        fake_service_clients = {
            'service1': [{'name': 'client1',
                          'service_version': 'client1.v1',
                          'module_path': 'I cannot load this',
                          'client_names': ['SomeClient1']}],
            'service2': [{'name': 'client2',
                          'service_version': 'client2.v1',
                          'module_path': 'This neither',
                          'client_names': ['SomeClient1']}]}
        msg = "(?=.*{0})(?=.*{1})".format(
            *[x[1][0]['module_path'] for x in fake_service_clients.items()])
        self.useFixture(fixtures.MockPatchObject(
            clients.ClientsRegistry(), 'get_service_clients',
            return_value=fake_service_clients))
        with testtools.ExpectedException(
                testtools.MultipleExceptions, value_re=msg):
            clients.ServiceClients(creds, identity_uri=uri)

    def test___init___plugin_service_clients_name_conflict(self):
        creds = fake_credentials.FakeKeystoneV3Credentials()
        uri = 'fake_uri'
        fake_service_clients = {
            'serviceA': [{'name': 'client1',
                          'service_version': 'client1.v1',
                          'module_path': 'fake_path_1',
                          'client_names': ['SomeClient1']}],
            'serviceB': [{'name': 'client1',
                          'service_version': 'client1.v2',
                          'module_path': 'fake_path_2',
                          'client_names': ['SomeClient2']}],
            'serviceC': [{'name': 'client1',
                          'service_version': 'client1.v1',
                          'module_path': 'fake_path_2',
                          'client_names': ['SomeClient1']}],
            'serviceD': [{'name': 'client1',
                          'service_version': 'client1.v2',
                          'module_path': 'fake_path_2',
                          'client_names': ['SomeClient2']}]}
        msg = "(?=.*{0})(?=.*{1})".format(
            *[x[1][0]['service_version'] for x in
                fake_service_clients.items()])
        self.useFixture(fixtures.MockPatchObject(
            clients.ClientsRegistry(), 'get_service_clients',
            return_value=fake_service_clients))
        with testtools.ExpectedException(
                testtools.MultipleExceptions, value_re=msg):
            clients.ServiceClients(creds, identity_uri=uri)

    def _get_manager(self, init_region='fake_region'):
        # Get a manager to invoke _setup_parameters on
        creds = fake_credentials.FakeKeystoneV2Credentials()
        return clients.ServiceClients(creds, identity_uri='fake_uri',
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

    def test_register_service_client_module(self):
        expected_params = {'fake_param1': 'fake_value1',
                           'fake_param2': 'fake_value2'}
        _manager = self._get_manager(init_region='fake_region_default')
        # Mock after the _manager is setup to preserve the call count
        factory_mock = self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory')).mock
        _manager.register_service_client_module(
            name='fake_module',
            service_version='fake_service',
            module_path='fake.path.to.module',
            client_names=[],
            **expected_params)
        self.assertThat(_manager, has_attribute('fake_module'))
        # Assert called once, without check for exact parameters
        self.assertTrue(factory_mock.called)
        self.assertEqual(1, factory_mock.call_count)
        # Assert expected params are in with their values
        actual_kwargs = factory_mock.call_args[1]
        self.assertIn('region', actual_kwargs)
        self.assertEqual('fake_region_default', actual_kwargs['region'])
        for param in expected_params:
            self.assertIn(param, actual_kwargs)
            self.assertEqual(expected_params[param], actual_kwargs[param])
        # Assert the new service is registered
        self.assertIn('fake_service', _manager._registered_services)

    def test_register_service_client_module_override_default(self):
        new_region = 'new_region'
        expected_params = {'fake_param1': 'fake_value1',
                           'fake_param2': 'fake_value2',
                           'region': new_region}
        _manager = self._get_manager(init_region='fake_region_default')
        # Mock after the _manager is setup to preserve the call count
        factory_mock = self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory')).mock
        _manager.register_service_client_module(
            name='fake_module',
            service_version='fake_service',
            module_path='fake.path.to.module',
            client_names=[],
            **expected_params)
        self.assertThat(_manager, has_attribute('fake_module'))
        # Assert called once, without check for exact parameters
        self.assertTrue(factory_mock.called)
        self.assertEqual(1, factory_mock.call_count)
        # Assert expected params are in with their values
        actual_kwargs = factory_mock.call_args[1]
        self.assertIn('region', actual_kwargs)
        self.assertEqual(new_region, actual_kwargs['region'])
        for param in expected_params:
            self.assertIn(param, actual_kwargs)
            self.assertEqual(expected_params[param], actual_kwargs[param])
        # Assert the new service is registered
        self.assertIn('fake_service', _manager._registered_services)

    def test_register_service_client_module_duplicate_name(self):
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory')).mock
        _manager = self._get_manager()
        name_owner = 'this_is_a_string'
        setattr(_manager, 'fake_module', name_owner)
        expected_error = '.*' + name_owner
        with testtools.ExpectedException(
                exceptions.ServiceClientRegistrationException, expected_error):
            _manager.register_service_client_module(
                name='fake_module', module_path='fake.path.to.module',
                service_version='fake_service', client_names=[])

    def test_register_service_client_module_duplicate_service(self):
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.clients.ClientsFactory')).mock
        _manager = self._get_manager()
        duplicate_service = 'fake_service1'
        expected_error = '.*' + duplicate_service
        _manager._registered_services = [duplicate_service]
        with testtools.ExpectedException(
                exceptions.ServiceClientRegistrationException, expected_error):
            _manager.register_service_client_module(
                name='fake_module', module_path='fake.path.to.module',
                service_version=duplicate_service, client_names=[])
