# Copyright 2014 IBM Corp.
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

import os
from unittest import mock

import fixtures
from oslo_serialization import jsonutils as json

from tempest import clients
from tempest.cmd import init
from tempest.cmd import verify_tempest_config
from tempest.common import credentials_factory
from tempest import config
from tempest.lib.common import rest_client
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest.tests import base
from tempest.tests import fake_config


class TestGetAPIVersions(base.TestCase):

    def test_remove_version_project(self):
        f = verify_tempest_config._remove_version_project
        self.assertEqual('/', f('/v2.1/%s/' % data_utils.rand_uuid_hex()))
        self.assertEqual('', f('/v2.1/tenant_id'))
        self.assertEqual('', f('/v3'))
        self.assertEqual('/', f('/v3/'))
        self.assertEqual('/something/', f('/something/v2.1/tenant_id/'))
        self.assertEqual('/something', f('/something/v2.1/tenant_id'))
        self.assertEqual('/something', f('/something/v3'))
        self.assertEqual('/something/', f('/something/v3/'))
        self.assertEqual('/', f('/'))  # http://localhost/
        self.assertEqual('', f(''))  # http://localhost

    def test_url_grab_versioned_nova_nossl(self):
        base_url = 'http://127.0.0.1:8774/v2/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('http://127.0.0.1:8774/', endpoint)

    def test_url_grab_versioned_nova_ssl(self):
        base_url = 'https://127.0.0.1:8774/v3/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('https://127.0.0.1:8774/', endpoint)

    def test_get_unversioned_endpoint_base(self):
        base_url = 'https://127.0.0.1:5000/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('https://127.0.0.1:5000/', endpoint)

    def test_get_unversioned_endpoint_subpath(self):
        base_url = 'https://127.0.0.1/identity/v3'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('https://127.0.0.1/identity', endpoint)

    def test_get_unversioned_endpoint_subpath_trailing_solidus(self):
        base_url = 'https://127.0.0.1/identity/v3/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('https://127.0.0.1/identity/', endpoint)


class TestDiscovery(base.TestCase):

    def setUp(self):
        super(TestDiscovery, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)

    def test_get_keystone_api_versions(self):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v2.0'}, {'id': 'v3.0'}]}}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.http.ClosingHttp.request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'keystone')
        self.assertIn('v2.0', versions)
        self.assertIn('v3.0', versions)

    def test_get_cinder_api_versions(self):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v1.0'}, {'id': 'v2.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.http.ClosingHttp.request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'cinder')
        self.assertIn('v1.0', versions)
        self.assertIn('v2.0', versions)

    def test_get_nova_versions(self):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}, {'id': 'v3.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.http.ClosingHttp.request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'nova')
        self.assertIn('v2.0', versions)
        self.assertIn('v3.0', versions)

    def test_get_versions_invalid_response(self):
        # When the response doesn't contain a JSON response, an error is
        # logged.
        mock_log_error = self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config.LOG, 'error')).mock

        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint'))

        # Simulated response is not JSON.
        sample_body = (
            '<html><head>Sample Response</head><body>This is the sample page '
            'for the web server. Why are you requesting it?</body></html>')
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.http.ClosingHttp.request',
            return_value=(None, sample_body)))

        # service value doesn't matter, just needs to match what
        # _get_api_versions puts in its client_dict.
        self.assertRaises(ValueError, verify_tempest_config._get_api_versions,
                          os=mock.MagicMock(), service='keystone')
        self.assertTrue(mock_log_error.called)

    def test_verify_api_versions(self):
        api_services = ['cinder', 'glance', 'keystone']
        fake_os = mock.MagicMock()
        for svc in api_services:
            m = 'verify_%s_api_versions' % svc
            with mock.patch.object(verify_tempest_config, m) as verify_mock:
                verify_tempest_config.verify_api_versions(fake_os, svc, True)
                verify_mock.assert_called_once_with(fake_os, True)

    def test_verify_api_versions_not_implemented(self):
        api_services = ['cinder', 'glance', 'keystone']
        fake_os = mock.MagicMock()
        for svc in api_services:
            m = 'verify_%s_api_versions' % svc
            with mock.patch.object(verify_tempest_config, m) as verify_mock:
                verify_tempest_config.verify_api_versions(fake_os, 'foo', True)
                self.assertFalse(verify_mock.called)

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_verify_keystone_api_versions_no_v3(self, mock_request):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v2.0'}]}}
        fake_resp = json.dumps(fake_resp)
        mock_request.return_value = (None, fake_resp)
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_keystone_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v3',
                                           'identity-feature-enabled',
                                           False, True)

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_verify_cinder_api_versions_no_v3(self, mock_request):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}]}
        fake_resp = json.dumps(fake_resp)
        mock_request.return_value = (None, fake_resp)
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_any_call('api_v3', 'volume-feature-enabled',
                                   False, True)
        self.assertEqual(1, print_mock.call_count)

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_verify_cinder_api_versions_no_v2(self, mock_request):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v3.0'}]}
        fake_resp = json.dumps(fake_resp)
        mock_request.return_value = (None, fake_resp)
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_any_call('api_v2', 'volume-feature-enabled',
                                   False, True)
        self.assertEqual(1, print_mock.call_count)

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_verify_cinder_api_versions_no_v1(self, mock_request):
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}, {'id': 'v3.0'}]}
        fake_resp = json.dumps(fake_resp)
        mock_request.return_value = (None, fake_resp)
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_not_called()

    def test_verify_glance_version_no_v2_with_v1_1(self):
        # This test verifies that wrong config api_v2 = True is detected
        class FakeClient(object):
            def get_versions(self):
                return (None, ['v1.1'])

        fake_os = mock.MagicMock()
        fake_module = mock.MagicMock()
        fake_module.ImagesClient = FakeClient
        fake_os.image_v1 = fake_module
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_with('api_v2', 'image-feature-enabled',
                                      False, True)

    def test_verify_glance_version_no_v2_with_v1_0(self):
        # This test verifies that wrong config api_v2 = True is detected
        class FakeClient(object):
            def get_versions(self):
                return (None, ['v1.0'])

        fake_os = mock.MagicMock()
        fake_module = mock.MagicMock()
        fake_module.ImagesClient = FakeClient
        fake_os.image_v1 = fake_module
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_with('api_v2', 'image-feature-enabled',
                                      False, True)

    def test_verify_glance_version_no_v1(self):
        # This test verifies that wrong config api_v1 = True is detected
        class FakeClient(object):
            def get_versions(self):
                raise lib_exc.NotFound()

            def list_versions(self):
                return {'versions': [{'id': 'v2.0'}]}

        fake_os = mock.MagicMock()
        fake_module = mock.MagicMock()
        fake_module.ImagesClient = FakeClient
        fake_module.VersionsClient = FakeClient
        fake_os.image_v1 = fake_module
        fake_os.image_v2 = fake_module
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_not_called()

    def test_verify_glance_version_no_version(self):
        # This test verifies that wrong config api_v1 = True is detected
        class FakeClient(object):
            def get_versions(self):
                raise lib_exc.NotFound()

            def list_versions(self):
                raise lib_exc.NotFound()

        fake_os = mock.MagicMock()
        fake_module = mock.MagicMock()
        fake_module.ImagesClient = FakeClient
        fake_module.VersionsClient = FakeClient
        fake_os.image_v1 = fake_module
        fake_os.image_v2 = fake_module
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('glance',
                                           'service-available',
                                           False, True)

    def test_verify_extensions_neutron(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['fake1', 'fake2', 'fake3'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'neutron', {})
        self.assertIn('neutron', results)
        self.assertIn('fake1', results['neutron'])
        self.assertTrue(results['neutron']['fake1'])
        self.assertIn('fake2', results['neutron'])
        self.assertTrue(results['neutron']['fake2'])
        self.assertIn('fake3', results['neutron'])
        self.assertFalse(results['neutron']['fake3'])
        self.assertIn('not_fake', results['neutron'])
        self.assertFalse(results['neutron']['not_fake'])

    def test_verify_extensions_neutron_all(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'neutron', {})
        self.assertIn('neutron', results)
        self.assertIn('extensions', results['neutron'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['neutron']['extensions']))

    def test_verify_extensions_neutron_none(self):
        def fake_list_extensions():
            return {'extensions': []}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'neutron', {})
        self.assertIn('neutron', results)
        self.assertIn('extensions', results['neutron'])
        self.assertEqual([], results['neutron']['extensions'])

    def test_verify_extensions_cinder(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['fake1', 'fake2', 'fake3'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'cinder', {})

        self.assertIn('cinder', results)
        self.assertIn('fake1', results['cinder'])
        self.assertTrue(results['cinder']['fake1'])
        self.assertIn('fake2', results['cinder'])
        self.assertTrue(results['cinder']['fake2'])
        self.assertIn('fake3', results['cinder'])
        self.assertFalse(results['cinder']['fake3'])
        self.assertIn('not_fake', results['cinder'])
        self.assertFalse(results['cinder']['not_fake'])

    def test_verify_extensions_cinder_all(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'cinder', {})
        self.assertIn('cinder', results)
        self.assertIn('extensions', results['cinder'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['cinder']['extensions']))

    def test_verify_extensions_cinder_none(self):
        def fake_list_extensions():
            return {'extensions': []}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'cinder', {})
        self.assertIn('cinder', results)
        self.assertIn('extensions', results['cinder'])
        self.assertEqual([], results['cinder']['extensions'])

    def test_verify_extensions_nova(self):
        def fake_list_extensions():
            return ([{'alias': 'fake1'}, {'alias': 'fake2'},
                     {'alias': 'not_fake'}])
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['fake1', 'fake2', 'fake3'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'nova', {})
        self.assertIn('nova', results)
        self.assertIn('fake1', results['nova'])
        self.assertTrue(results['nova']['fake1'])
        self.assertIn('fake2', results['nova'])
        self.assertTrue(results['nova']['fake2'])
        self.assertIn('fake3', results['nova'])
        self.assertFalse(results['nova']['fake3'])
        self.assertIn('not_fake', results['nova'])
        self.assertFalse(results['nova']['not_fake'])

    def test_verify_extensions_nova_all(self):
        def fake_list_extensions():
            return ({'extensions': [{'alias': 'fake1'},
                                    {'alias': 'fake2'},
                                    {'alias': 'not_fake'}]})
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'nova', {})
        self.assertIn('nova', results)
        self.assertIn('extensions', results['nova'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['nova']['extensions']))

    def test_verify_extensions_nova_none(self):
        def fake_list_extensions():
            return ({'extensions': []})
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_extensions = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'nova', {})
        self.assertIn('nova', results)
        self.assertIn('extensions', results['nova'])
        self.assertEqual([], results['nova']['extensions'])

    def test_verify_extensions_swift(self):
        def fake_list_extensions():
            return {'fake1': 'metadata',
                    'fake2': 'metadata',
                    'not_fake': 'metadata',
                    'swift': 'metadata'}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_capabilities = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['fake1', 'fake2', 'fake3'])))
        results = verify_tempest_config.verify_extensions(fake_os, 'swift', {})
        self.assertIn('swift', results)
        self.assertIn('fake1', results['swift'])
        self.assertTrue(results['swift']['fake1'])
        self.assertIn('fake2', results['swift'])
        self.assertTrue(results['swift']['fake2'])
        self.assertIn('fake3', results['swift'])
        self.assertFalse(results['swift']['fake3'])
        self.assertIn('not_fake', results['swift'])
        self.assertFalse(results['swift']['not_fake'])

    def test_verify_extensions_swift_all(self):
        def fake_list_extensions():
            return {'fake1': 'metadata',
                    'fake2': 'metadata',
                    'not_fake': 'metadata',
                    'swift': 'metadata'}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_capabilities = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'swift', {})
        self.assertIn('swift', results)
        self.assertIn('extensions', results['swift'])
        self.assertEqual(sorted(['not_fake', 'fake1', 'fake2']),
                         sorted(results['swift']['extensions']))

    def test_verify_extensions_swift_none(self):
        def fake_list_extensions():
            return {'swift': 'metadata'}
        fake_os = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_client.list_capabilities = fake_list_extensions
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_extension_client',
            return_value=fake_client))
        self.useFixture(fixtures.MockPatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'swift', {})
        self.assertIn('swift', results)
        self.assertIn('extensions', results['swift'])
        self.assertEqual([], results['swift']['extensions'])

    def test_get_extension_client(self):
        creds = credentials_factory.get_credentials(
            fill_in=False, username='fake_user', project_name='fake_project',
            password='fake_password')
        os = clients.Manager(creds)
        for service in ['nova', 'neutron', 'swift', 'cinder']:
            extensions_client = verify_tempest_config.get_extension_client(
                os, service)
            self.assertIsInstance(extensions_client, rest_client.RestClient)

    def test_get_extension_client_sysexit(self):
        creds = credentials_factory.get_credentials(
            fill_in=False, username='fake_user', project_name='fake_project',
            password='fake_password')
        os = clients.Manager(creds)
        self.assertRaises(SystemExit,
                          verify_tempest_config.get_extension_client,
                          os, 'fakeservice')

    def test_get_config_file(self):
        conf_dir = os.path.join(os.getcwd(), 'etc')
        conf_file = "tempest.conf.sample"
        local_sample_conf_file = os.path.join(conf_dir, conf_file)

        def fake_environ_get(key, default=None):
            if key == 'TEMPEST_CONFIG_DIR':
                return conf_dir
            elif key == 'TEMPEST_CONFIG':
                return 'tempest.conf.sample'
            return default

        with mock.patch('os.environ.get', side_effect=fake_environ_get,
                        autospec=True):
            init_cmd = init.TempestInit(None, None)
            init_cmd.generate_sample_config(os.path.join(conf_dir, os.pardir))
            self.assertTrue(os.path.isfile(local_sample_conf_file),
                            local_sample_conf_file)

            file_pointer = verify_tempest_config._get_config_file()
            self.assertEqual(local_sample_conf_file, file_pointer.name)

            with open(local_sample_conf_file, 'r+') as f:
                local_sample_conf_contents = f.read()
            self.assertEqual(local_sample_conf_contents, file_pointer.read())

            if file_pointer:
                file_pointer.close()

    def test_print_and_or_update_true(self):
        with mock.patch.object(
            verify_tempest_config, 'change_option') as test_mock:
            verify_tempest_config.print_and_or_update(
                'fakeservice', 'fake-service-available', False, True)
            test_mock.assert_called_once_with(
                'fakeservice', 'fake-service-available', False)

    def test_print_and_or_update_false(self):
        with mock.patch.object(
            verify_tempest_config, 'change_option') as test_mock:
            verify_tempest_config.print_and_or_update(
                'fakeservice', 'fake-service-available', False, False)
            test_mock.assert_not_called()

    def test_contains_version_positive_data(self):
        self.assertTrue(
            verify_tempest_config.contains_version('v1.', ['v1.0', 'v2.0']))

    def test_contains_version_negative_data(self):
        self.assertFalse(
            verify_tempest_config.contains_version('v5.', ['v1.0', 'v2.0']))

    def test_check_service_availability(self):
        class FakeAuthProvider:
            def get_auth(self):
                return ('token',
                        {'serviceCatalog': [{'type': 'compute'},
                                            {'type': 'image'},
                                            {'type': 'volumev3'},
                                            {'type': 'network'},
                                            {'type': 'object-store'}]})

        class Fake_os:
            auth_provider = FakeAuthProvider()
            auth_version = 'v2'
        verify_tempest_config.CONF._config = fake_config.FakePrivate()
        services = verify_tempest_config.check_service_availability(
            Fake_os(), True)
        self.assertEqual(
            sorted(['nova', 'glance', 'neutron', 'swift', 'cinder']),
            sorted(services))
