# Copyright 2014 IBM Corp.
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

import copy

from tempest import auth
from tempest.common import http
from tempest import config
from tempest import exceptions
from tempest.openstack.common.fixture import mockpatch
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests import fake_http
from tempest.tests import fake_identity


class BaseAuthTestsSetUp(base.TestCase):
    _auth_provider_class = None
    credentials = {
        'username': 'fake_user',
        'password': 'fake_pwd',
        'tenant_name': 'fake_tenant'
    }

    def _auth(self, credentials, **params):
        """
        returns auth method according to keystone
        """
        return self._auth_provider_class(credentials, **params)

    def setUp(self):
        super(BaseAuthTestsSetUp, self).setUp()
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakeConfig)
        self.fake_http = fake_http.fake_httplib2(return_type=200)
        self.stubs.Set(http.ClosingHttp, 'request', self.fake_http.request)
        self.auth_provider = self._auth(self.credentials)


class TestBaseAuthProvider(BaseAuthTestsSetUp):
    """
    This tests auth.AuthProvider class which is base for the other so we
    obviously don't test not implemented method or the ones which strongly
    depends on them.
    """
    _auth_provider_class = auth.AuthProvider

    def test_check_credentials_is_dict(self):
        self.assertTrue(self.auth_provider.check_credentials({}))

    def test_check_credentials_bad_type(self):
        self.assertFalse(self.auth_provider.check_credentials([]))

    def test_instantiate_with_bad_credentials_type(self):
        """
        Assure that credentials with bad type fail with TypeError
        """
        self.assertRaises(TypeError, self._auth, [])

    def test_auth_data_property(self):
        self.assertRaises(NotImplementedError, getattr, self.auth_provider,
                          'auth_data')

    def test_auth_data_property_when_cache_exists(self):
        self.auth_provider.cache = 'foo'
        self.useFixture(mockpatch.PatchObject(self.auth_provider,
                                              'is_expired',
                                              return_value=False))
        self.assertEqual('foo', getattr(self.auth_provider, 'auth_data'))

    def test_delete_auth_data_property_through_deleter(self):
        self.auth_provider.cache = 'foo'
        del self.auth_provider.auth_data
        self.assertIsNone(self.auth_provider.cache)

    def test_delete_auth_data_property_through_clear_auth(self):
        self.auth_provider.cache = 'foo'
        self.auth_provider.clear_auth()
        self.assertIsNone(self.auth_provider.cache)

    def test_set_and_reset_alt_auth_data(self):
        self.auth_provider.set_alt_auth_data('foo', 'bar')
        self.assertEqual(self.auth_provider.alt_part, 'foo')
        self.assertEqual(self.auth_provider.alt_auth_data, 'bar')

        self.auth_provider.reset_alt_auth_data()
        self.assertIsNone(self.auth_provider.alt_part)
        self.assertIsNone(self.auth_provider.alt_auth_data)


class TestKeystoneV2AuthProvider(BaseAuthTestsSetUp):
    _auth_provider_class = auth.KeystoneV2AuthProvider

    def setUp(self):
        super(TestKeystoneV2AuthProvider, self).setUp()
        self.stubs.Set(http.ClosingHttp, 'request',
                       fake_identity._fake_v2_response)
        self.target_url = 'test_api'

    def _get_fake_alt_identity(self):
        return fake_identity.ALT_IDENTITY_V2_RESPONSE['access']

    def _get_result_url_from_fake_identity(self):
        return fake_identity.COMPUTE_ENDPOINTS_V2['endpoints'][1]['publicURL']

    def _get_token_from_fake_identity(self):
        return fake_identity.TOKEN

    def _test_request_helper(self):
        filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }

        url, headers, body = self.auth_provider.auth_request('GET',
                                                             self.target_url,
                                                             filters=filters)

        result_url = self._get_result_url_from_fake_identity()
        self.assertEqual(url, result_url + '/' + self.target_url)
        self.assertEqual(self._get_token_from_fake_identity(),
                         headers['X-Auth-Token'])
        self.assertEqual(body, None)

    def test_request(self):
        self._test_request_helper()

    def test_request_with_alt_auth(self):
        self.auth_provider.set_alt_auth_data(
            'body',
            (fake_identity.ALT_TOKEN, self._get_fake_alt_identity()))
        self._test_request_helper()
        # Assert alt auth data is clear after it
        self.assertIsNone(self.auth_provider.alt_part)
        self.assertIsNone(self.auth_provider.alt_auth_data)

    def test_request_with_bad_service(self):
        filters = {
            'service': 'BAD_SERVICE',
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self.auth_provider.auth_request, 'GET',
                          'http://fakeurl.com/fake_api', filters=filters)

    def test_request_without_service(self):
        filters = {
            'service': None,
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self.auth_provider.auth_request, 'GET',
                          'http://fakeurl.com/fake_api', filters=filters)

    def test_check_credentials_missing_attribute(self):
        for attr in ['username', 'password']:
            cred = copy.copy(self.credentials)
            del cred[attr]
            self.assertFalse(self.auth_provider.check_credentials(cred))

    def test_check_credentials_not_scoped_missing_tenant_name(self):
        cred = copy.copy(self.credentials)
        del cred['tenant_name']
        self.assertTrue(self.auth_provider.check_credentials(cred,
                                                             scoped=False))

    def test_check_credentials_missing_tenant_name(self):
        cred = copy.copy(self.credentials)
        del cred['tenant_name']
        self.assertFalse(self.auth_provider.check_credentials(cred))


class TestKeystoneV3AuthProvider(TestKeystoneV2AuthProvider):
    _auth_provider_class = auth.KeystoneV3AuthProvider
    credentials = {
        'username': 'fake_user',
        'password': 'fake_pwd',
        'tenant_name': 'fake_tenant',
        'domain_name': 'fake_domain_name',
    }

    def setUp(self):
        super(TestKeystoneV3AuthProvider, self).setUp()
        self.stubs.Set(http.ClosingHttp, 'request',
                       fake_identity._fake_v3_response)

    def _get_fake_alt_identity(self):
        return fake_identity.ALT_IDENTITY_V3['token']

    def _get_result_url_from_fake_identity(self):
        return fake_identity.COMPUTE_ENDPOINTS_V3['endpoints'][1]['url']

    def test_check_credentials_missing_tenant_name(self):
        cred = copy.copy(self.credentials)
        del cred['domain_name']
        self.assertFalse(self.auth_provider.check_credentials(cred))
