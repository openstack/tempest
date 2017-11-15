# Copyright 2017 IBM Corp.
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

import mock
from oslo_config import cfg
import testtools

from tempest.common import credentials_factory as cf
from tempest import config
from tempest.lib.common import dynamic_creds
from tempest.lib.common import preprov_creds
from tempest.lib import exceptions
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests.lib import fake_credentials


class TestCredentialsFactory(base.TestCase):

    def setUp(self):
        super(TestCredentialsFactory, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

    def test_get_dynamic_provider_params_creds_v2(self):
        expected_uri = 'EXPECTED_V2_URI'
        cfg.CONF.set_default('uri', expected_uri, group='identity')
        admin_creds = fake_credentials.FakeCredentials()
        params = cf.get_dynamic_provider_params('v2', admin_creds=admin_creds)
        expected_params = dict(identity_uri=expected_uri,
                               admin_creds=admin_creds)
        for key in expected_params:
            self.assertIn(key, params)
            self.assertEqual(expected_params[key], params[key])

    def test_get_dynamic_provider_params_creds_v3(self):
        expected_uri = 'EXPECTED_V3_URI'
        cfg.CONF.set_default('uri_v3', expected_uri, group='identity')
        admin_creds = fake_credentials.FakeCredentials()
        params = cf.get_dynamic_provider_params('v3', admin_creds=admin_creds)
        expected_params = dict(identity_uri=expected_uri,
                               admin_creds=admin_creds)
        for key in expected_params:
            self.assertIn(key, params)
            self.assertEqual(expected_params[key], params[key])

    def test_get_dynamic_provider_params_creds_vx(self):
        admin_creds = fake_credentials.FakeCredentials()
        invalid_version = 'invalid_version_x'
        with testtools.ExpectedException(
                exc_type=exceptions.InvalidIdentityVersion,
                value_re='Invalid version ' + invalid_version):
            cf.get_dynamic_provider_params(invalid_version,
                                           admin_creds=admin_creds)

    def test_get_dynamic_provider_params_no_creds(self):
        expected_identity_version = 'v3'
        with mock.patch.object(
                cf, 'get_configured_admin_credentials') as admin_creds_mock:
            cf.get_dynamic_provider_params(expected_identity_version)
            admin_creds_mock.assert_called_once_with(
                fill_in=True, identity_version=expected_identity_version)

    def test_get_preprov_provider_params_creds_v2(self):
        expected_uri = 'EXPECTED_V2_URI'
        cfg.CONF.set_default('uri', expected_uri, group='identity')
        params = cf.get_preprov_provider_params('v2')
        self.assertIn('identity_uri', params)
        self.assertEqual(expected_uri, params['identity_uri'])

    def test_get_preprov_provider_params_creds_v3(self):
        expected_uri = 'EXPECTED_V3_URI'
        cfg.CONF.set_default('uri_v3', expected_uri, group='identity')
        params = cf.get_preprov_provider_params('v3')
        self.assertIn('identity_uri', params)
        self.assertEqual(expected_uri, params['identity_uri'])

    def test_get_preprov_provider_params_creds_vx(self):
        invalid_version = 'invalid_version_x'
        with testtools.ExpectedException(
                exc_type=exceptions.InvalidIdentityVersion,
                value_re='Invalid version ' + invalid_version):
            cf.get_dynamic_provider_params(invalid_version)

    @mock.patch.object(dynamic_creds, 'DynamicCredentialProvider')
    @mock.patch.object(cf, 'get_dynamic_provider_params')
    def test_get_credentials_provider_dynamic(
            self, mock_dynamic_provider_params,
            mock_dynamic_credentials_provider_class):
        cfg.CONF.set_default('use_dynamic_credentials', True, group='auth')
        expected_params = {'foo': 'bar'}
        mock_dynamic_provider_params.return_value = expected_params
        expected_name = 'my_name'
        expected_network_resources = {'network': 'resources'}
        expected_identity_version = 'identity_version'
        cf.get_credentials_provider(
            expected_name,
            network_resources=expected_network_resources,
            force_tenant_isolation=False,
            identity_version=expected_identity_version)
        mock_dynamic_provider_params.assert_called_once_with(
            expected_identity_version)
        mock_dynamic_credentials_provider_class.assert_called_once_with(
            name=expected_name, network_resources=expected_network_resources,
            **expected_params)

    @mock.patch.object(preprov_creds, 'PreProvisionedCredentialProvider')
    @mock.patch.object(cf, 'get_preprov_provider_params')
    def test_get_credentials_provider_preprov(
            self, mock_preprov_provider_params,
            mock_preprov_credentials_provider_class):
        cfg.CONF.set_default('use_dynamic_credentials', False, group='auth')
        cfg.CONF.set_default('test_accounts_file', '/some/file', group='auth')
        expected_params = {'foo': 'bar'}
        mock_preprov_provider_params.return_value = expected_params
        expected_name = 'my_name'
        expected_identity_version = 'identity_version'
        cf.get_credentials_provider(
            expected_name,
            force_tenant_isolation=False,
            identity_version=expected_identity_version)
        mock_preprov_provider_params.assert_called_once_with(
            expected_identity_version)
        mock_preprov_credentials_provider_class.assert_called_once_with(
            name=expected_name, **expected_params)

    def test_get_credentials_provider_preprov_no_file(self):
        cfg.CONF.set_default('use_dynamic_credentials', False, group='auth')
        cfg.CONF.set_default('test_accounts_file', None, group='auth')
        with testtools.ExpectedException(
                exc_type=exceptions.InvalidConfiguration):
            cf.get_credentials_provider(
                'some_name',
                force_tenant_isolation=False,
                identity_version='some_version')

    @mock.patch.object(dynamic_creds, 'DynamicCredentialProvider')
    @mock.patch.object(cf, 'get_dynamic_provider_params')
    def test_get_credentials_provider_force_dynamic(
            self, mock_dynamic_provider_params,
            mock_dynamic_credentials_provider_class):
        cfg.CONF.set_default('use_dynamic_credentials', False, group='auth')
        expected_params = {'foo': 'bar'}
        mock_dynamic_provider_params.return_value = expected_params
        expected_name = 'my_name'
        expected_network_resources = {'network': 'resources'}
        expected_identity_version = 'identity_version'
        cf.get_credentials_provider(
            expected_name,
            network_resources=expected_network_resources,
            force_tenant_isolation=True,
            identity_version=expected_identity_version)
        mock_dynamic_provider_params.assert_called_once_with(
            expected_identity_version)
        mock_dynamic_credentials_provider_class.assert_called_once_with(
            name=expected_name, network_resources=expected_network_resources,
            **expected_params)

    @mock.patch.object(cf, 'get_credentials')
    def test_get_configured_admin_credentials(self, mock_get_credentials):
        cfg.CONF.set_default('auth_version', 'v3', 'identity')
        all_params = [('admin_username', 'username', 'my_name'),
                      ('admin_password', 'password', 'secret'),
                      ('admin_project_name', 'project_name', 'my_pname'),
                      ('admin_domain_name', 'domain_name', 'my_dname')]
        expected_result = 'my_admin_credentials'
        mock_get_credentials.return_value = expected_result
        for config_item, _, value in all_params:
            cfg.CONF.set_default(config_item, value, 'auth')
        # Build the expected params
        expected_params = dict(
            [(field, value) for _, field, value in all_params])
        expected_params.update(config.service_client_config())
        admin_creds = cf.get_configured_admin_credentials()
        mock_get_credentials.assert_called_once_with(
            fill_in=True, identity_version='v3', **expected_params)
        self.assertEqual(expected_result, admin_creds)

    @mock.patch.object(cf, 'get_credentials')
    def test_get_configured_admin_credentials_not_fill_valid(
            self, mock_get_credentials):
        cfg.CONF.set_default('auth_version', 'v2', 'identity')
        all_params = [('admin_username', 'username', 'my_name'),
                      ('admin_password', 'password', 'secret'),
                      ('admin_project_name', 'project_name', 'my_pname'),
                      ('admin_domain_name', 'domain_name', 'my_dname')]
        expected_result = mock.Mock()
        expected_result.is_valid.return_value = True
        mock_get_credentials.return_value = expected_result
        for config_item, _, value in all_params:
            cfg.CONF.set_default(config_item, value, 'auth')
        # Build the expected params
        expected_params = dict(
            [(field, value) for _, field, value in all_params])
        expected_params.update(config.service_client_config())
        admin_creds = cf.get_configured_admin_credentials(
            fill_in=False, identity_version='v3')
        mock_get_credentials.assert_called_once_with(
            fill_in=False, identity_version='v3', **expected_params)
        self.assertEqual(expected_result, admin_creds)
        expected_result.is_valid.assert_called_once()

    @mock.patch.object(cf, 'get_credentials')
    def test_get_configured_admin_credentials_not_fill_not_valid(
            self, mock_get_credentials):
        cfg.CONF.set_default('auth_version', 'v2', 'identity')
        expected_result = mock.Mock()
        expected_result.is_valid.return_value = False
        mock_get_credentials.return_value = expected_result
        with testtools.ExpectedException(exceptions.InvalidConfiguration,
                                         value_re='.*\n.*identity version v2'):
            cf.get_configured_admin_credentials(fill_in=False)

    @mock.patch('tempest.lib.auth.get_credentials')
    def test_get_credentials_v2(self, mock_auth_get_credentials):
        expected_uri = 'V2_URI'
        expected_result = 'my_creds'
        mock_auth_get_credentials.return_value = expected_result
        cfg.CONF.set_default('uri', expected_uri, 'identity')
        params = {'foo': 'bar'}
        expected_params = params.copy()
        expected_params.update(config.service_client_config())
        result = cf.get_credentials(identity_version='v2', **params)
        self.assertEqual(expected_result, result)
        mock_auth_get_credentials.assert_called_once_with(
            expected_uri, fill_in=True, identity_version='v2',
            **expected_params)

    @mock.patch('tempest.lib.auth.get_credentials')
    def test_get_credentials_v3_no_domain(self, mock_auth_get_credentials):
        expected_uri = 'V3_URI'
        expected_result = 'my_creds'
        expected_domain = 'my_domain'
        mock_auth_get_credentials.return_value = expected_result
        cfg.CONF.set_default('uri_v3', expected_uri, 'identity')
        cfg.CONF.set_default('default_credentials_domain_name',
                             expected_domain, 'auth')
        params = {'foo': 'bar'}
        expected_params = params.copy()
        expected_params['domain_name'] = expected_domain
        expected_params.update(config.service_client_config())
        result = cf.get_credentials(fill_in=False, identity_version='v3',
                                    **params)
        self.assertEqual(expected_result, result)
        mock_auth_get_credentials.assert_called_once_with(
            expected_uri, fill_in=False, identity_version='v3',
            **expected_params)

    @mock.patch('tempest.lib.auth.get_credentials')
    def test_get_credentials_v3_domain(self, mock_auth_get_credentials):
        expected_uri = 'V3_URI'
        expected_result = 'my_creds'
        expected_domain = 'my_domain'
        mock_auth_get_credentials.return_value = expected_result
        cfg.CONF.set_default('uri_v3', expected_uri, 'identity')
        cfg.CONF.set_default('default_credentials_domain_name',
                             expected_domain, 'auth')
        params = {'foo': 'bar', 'user_domain_name': expected_domain}
        expected_params = params.copy()
        expected_params.update(config.service_client_config())
        result = cf.get_credentials(fill_in=False, identity_version='v3',
                                    **params)
        self.assertEqual(expected_result, result)
        mock_auth_get_credentials.assert_called_once_with(
            expected_uri, fill_in=False, identity_version='v3',
            **expected_params)
