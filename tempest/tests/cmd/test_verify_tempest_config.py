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

import json

import mock
from oslotest import mockpatch

from tempest.cmd import verify_tempest_config
from tempest import config
from tempest.tests import base
from tempest.tests import fake_config


class TestGetAPIVersions(base.TestCase):

    def test_url_grab_versioned_nova_nossl(self):
        base_url = 'http://127.0.0.1:8774/v2/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('http://127.0.0.1:8774', endpoint)

    def test_url_grab_versioned_nova_ssl(self):
        base_url = 'https://127.0.0.1:8774/v3/'
        endpoint = verify_tempest_config._get_unversioned_endpoint(base_url)
        self.assertEqual('https://127.0.0.1:8774', endpoint)


class TestDiscovery(base.TestCase):

    def setUp(self):
        super(TestDiscovery, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)

    def test_get_keystone_api_versions(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v2.0'}, {'id': 'v3.0'}]}}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'keystone')
        self.assertIn('v2.0', versions)
        self.assertIn('v3.0', versions)

    def test_get_cinder_api_versions(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v1.0'}, {'id': 'v2.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'cinder')
        self.assertIn('v1.0', versions)
        self.assertIn('v2.0', versions)

    def test_get_nova_versions(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}, {'id': 'v3.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'nova')
        self.assertIn('v2.0', versions)
        self.assertIn('v3.0', versions)

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

    def test_verify_keystone_api_versions_no_v3(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v2.0'}]}}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_keystone_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v3',
                                           'identity_feature_enabled',
                                           False, True)

    def test_verify_keystone_api_versions_no_v2(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v3.0'}]}}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_keystone_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2',
                                           'identity_feature_enabled',
                                           False, True)

    def test_verify_cinder_api_versions_no_v2(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v1.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2', 'volume_feature_enabled',
                                           False, True)

    def test_verify_cinder_api_versions_no_v1(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.Patch('httplib2.Http.request',
                                        return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v1', 'volume_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v2_with_v1_1(self):
        def fake_get_versions():
            return (['v1.1'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2', 'image_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v2_with_v1_0(self):
        def fake_get_versions():
            return (['v1.0'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2', 'image_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v1(self):
        def fake_get_versions():
            return (['v2.0'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v1', 'image_feature_enabled',
                                           False, True)

    def test_verify_extensions_neutron(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_os.network_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
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
        fake_os.network_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'neutron', {})
        self.assertIn('neutron', results)
        self.assertIn('extensions', results['neutron'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['neutron']['extensions']))

    def test_verify_extensions_cinder(self):
        def fake_list_extensions():
            return {'extensions': [{'alias': 'fake1'},
                                   {'alias': 'fake2'},
                                   {'alias': 'not_fake'}]}
        fake_os = mock.MagicMock()
        fake_os.volumes_extension_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
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
        fake_os.volumes_extension_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'cinder', {})
        self.assertIn('cinder', results)
        self.assertIn('extensions', results['cinder'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['cinder']['extensions']))

    def test_verify_extensions_nova(self):
        def fake_list_extensions():
            return ([{'alias': 'fake1'}, {'alias': 'fake2'},
                     {'alias': 'not_fake'}])
        fake_os = mock.MagicMock()
        fake_os.extensions_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
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
        fake_os.extensions_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'nova', {})
        self.assertIn('nova', results)
        self.assertIn('extensions', results['nova'])
        self.assertEqual(sorted(['fake1', 'fake2', 'not_fake']),
                         sorted(results['nova']['extensions']))

    def test_verify_extensions_swift(self):
        def fake_list_extensions():
            return (None, {'fake1': 'metadata',
                           'fake2': 'metadata',
                           'not_fake': 'metadata',
                           'swift': 'metadata'})
        fake_os = mock.MagicMock()
        fake_os.account_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
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
            return (None, {'fake1': 'metadata',
                           'fake2': 'metadata',
                           'not_fake': 'metadata',
                           'swift': 'metadata'})
        fake_os = mock.MagicMock()
        fake_os.account_client.list_extensions = fake_list_extensions
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, 'get_enabled_extensions',
            return_value=(['all'])))
        results = verify_tempest_config.verify_extensions(fake_os,
                                                          'swift', {})
        self.assertIn('swift', results)
        self.assertIn('extensions', results['swift'])
        self.assertEqual(sorted(['not_fake', 'fake1', 'fake2']),
                         sorted(results['swift']['extensions']))
