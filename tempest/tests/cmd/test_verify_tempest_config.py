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

from tempest.cmd import verify_tempest_config
from tempest import config
from tempest.openstack.common.fixture import mockpatch
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        versions = verify_tempest_config._get_api_versions(fake_os, 'nova')
        self.assertIn('v2.0', versions)
        self.assertIn('v3.0', versions)

    def test_verify_keystone_api_versions_no_v3(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': {'values': [{'id': 'v2.0'}]}}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
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
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_cinder_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v1', 'volume_feature_enabled',
                                           False, True)

    def test_verify_nova_versions(self):
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config, '_get_unversioned_endpoint',
            return_value='http://fake_endpoint:5000'))
        fake_resp = {'versions': [{'id': 'v2.0'}]}
        fake_resp = json.dumps(fake_resp)
        self.useFixture(mockpatch.PatchObject(
            verify_tempest_config.RAW_HTTP, 'request',
            return_value=(None, fake_resp)))
        fake_os = mock.MagicMock()
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_nova_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v3', 'compute_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v2_with_v1_1(self):
        def fake_get_versions():
            return (None, ['v1.1'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2', 'image_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v2_with_v1_0(self):
        def fake_get_versions():
            return (None, ['v1.0'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v2', 'image_feature_enabled',
                                           False, True)

    def test_verify_glance_version_no_v1(self):
        def fake_get_versions():
            return (None, ['v2.0'])
        fake_os = mock.MagicMock()
        fake_os.image_client.get_versions = fake_get_versions
        with mock.patch.object(verify_tempest_config,
                               'print_and_or_update') as print_mock:
            verify_tempest_config.verify_glance_api_versions(fake_os, True)
        print_mock.assert_called_once_with('api_v1', 'image_feature_enabled',
                                           False, True)
