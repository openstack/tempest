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
import datetime

from oslotest import mockpatch

from tempest import auth
from tempest import exceptions
from tempest.services.identity.v2.json import token_client as v2_client
from tempest.services.identity.v3.json import token_client as v3_client
from tempest.tests import base
from tempest.tests import fake_credentials
from tempest.tests import fake_http
from tempest.tests import fake_identity


def fake_get_credentials(fill_in=True, identity_version='v2', **kwargs):
    return fake_credentials.FakeCredentials()


class BaseAuthTestsSetUp(base.TestCase):
    _auth_provider_class = None
    credentials = fake_credentials.FakeCredentials()

    def _auth(self, credentials, auth_url, **params):
        """
        returns auth method according to keystone
        """
        return self._auth_provider_class(credentials, auth_url, **params)

    def setUp(self):
        super(BaseAuthTestsSetUp, self).setUp()
        self.fake_http = fake_http.fake_httplib2(return_type=200)
        self.stubs.Set(auth, 'get_credentials', fake_get_credentials)
        self.auth_provider = self._auth(self.credentials,
                                        fake_identity.FAKE_AUTH_URL)


class TestBaseAuthProvider(BaseAuthTestsSetUp):
    """
    This tests auth.AuthProvider class which is base for the other so we
    obviously don't test not implemented method or the ones which strongly
    depends on them.
    """

    class FakeAuthProviderImpl(auth.AuthProvider):
        def _decorate_request():
            pass

        def _fill_credentials():
            pass

        def _get_auth():
            pass

        def base_url():
            pass

        def is_expired():
            pass

    _auth_provider_class = FakeAuthProviderImpl

    def _auth(self, credentials, auth_url, **params):
        """
        returns auth method according to keystone
        """
        return self._auth_provider_class(credentials, **params)

    def test_check_credentials_bad_type(self):
        self.assertFalse(self.auth_provider.check_credentials([]))

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

    def test_auth_class(self):
        self.assertRaises(TypeError,
                          auth.AuthProvider,
                          fake_credentials.FakeCredentials)


class TestKeystoneV2AuthProvider(BaseAuthTestsSetUp):
    _endpoints = fake_identity.IDENTITY_V2_RESPONSE['access']['serviceCatalog']
    _auth_provider_class = auth.KeystoneV2AuthProvider
    credentials = fake_credentials.FakeKeystoneV2Credentials()

    def setUp(self):
        super(TestKeystoneV2AuthProvider, self).setUp()
        self.stubs.Set(v2_client.TokenClientJSON, 'raw_request',
                       fake_identity._fake_v2_response)
        self.target_url = 'test_api'

    def _get_fake_alt_identity(self):
        return fake_identity.ALT_IDENTITY_V2_RESPONSE['access']

    def _get_result_url_from_endpoint(self, ep, endpoint_type='publicURL',
                                      replacement=None):
        if replacement:
            return ep[endpoint_type].replace('v2', replacement)
        return ep[endpoint_type]

    def _get_token_from_fake_identity(self):
        return fake_identity.TOKEN

    def _get_from_fake_identity(self, attr):
        access = fake_identity.IDENTITY_V2_RESPONSE['access']
        if attr == 'user_id':
            return access['user']['id']
        elif attr == 'tenant_id':
            return access['token']['tenant']['id']

    def _test_request_helper(self, filters, expected):
        url, headers, body = self.auth_provider.auth_request('GET',
                                                             self.target_url,
                                                             filters=filters)

        self.assertEqual(expected['url'], url)
        self.assertEqual(expected['token'], headers['X-Auth-Token'])
        self.assertEqual(expected['body'], body)

    def _auth_data_with_expiry(self, date_as_string):
        token, access = self.auth_provider.auth_data
        access['token']['expires'] = date_as_string
        return token, access

    def test_request(self):
        filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion'
        }

        url = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][1]) + '/' + self.target_url

        expected = {
            'body': None,
            'url': url,
            'token': self._get_token_from_fake_identity(),
        }
        self._test_request_helper(filters, expected)

    def test_request_with_alt_auth_cleans_alt(self):
        self.auth_provider.set_alt_auth_data(
            'body',
            (fake_identity.ALT_TOKEN, self._get_fake_alt_identity()))
        self.test_request()
        # Assert alt auth data is clear after it
        self.assertIsNone(self.auth_provider.alt_part)
        self.assertIsNone(self.auth_provider.alt_auth_data)

    def test_request_with_alt_part_without_alt_data(self):
        """
        Assert that when alt_part is defined, the corresponding original
        request element is kept the same.
        """
        filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }
        self.auth_provider.set_alt_auth_data('url', None)

        url, headers, body = self.auth_provider.auth_request('GET',
                                                             self.target_url,
                                                             filters=filters)

        self.assertEqual(url, self.target_url)
        self.assertEqual(self._get_token_from_fake_identity(),
                         headers['X-Auth-Token'])
        self.assertEqual(body, None)

    def test_request_with_bad_service(self):
        filters = {
            'service': 'BAD_SERVICE',
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self.auth_provider.auth_request, 'GET',
                          self.target_url, filters=filters)

    def test_request_without_service(self):
        filters = {
            'service': None,
            'endpoint_type': 'publicURL',
            'region': 'fakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self.auth_provider.auth_request, 'GET',
                          self.target_url, filters=filters)

    def test_check_credentials_missing_attribute(self):
        for attr in ['username', 'password']:
            cred = copy.copy(self.credentials)
            del cred[attr]
            self.assertFalse(self.auth_provider.check_credentials(cred))

    def test_fill_credentials(self):
        self.auth_provider.fill_credentials()
        creds = self.auth_provider.credentials
        for attr in ['user_id', 'tenant_id']:
            self.assertEqual(self._get_from_fake_identity(attr),
                             getattr(creds, attr))

    def _test_base_url_helper(self, expected_url, filters,
                              auth_data=None):

        url = self.auth_provider.base_url(filters, auth_data)
        self.assertEqual(url, expected_url)

    def test_base_url(self):
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion'
        }
        expected = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][1])
        self._test_base_url_helper(expected, self.filters)

    def test_base_url_to_get_admin_endpoint(self):
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'adminURL',
            'region': 'FakeRegion'
        }
        expected = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][1], endpoint_type='adminURL')
        self._test_base_url_helper(expected, self.filters)

    def test_base_url_unknown_region(self):
        """
        Assure that if the region is unknow the first endpoint is returned.
        """
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'AintNoBodyKnowThisRegion'
        }
        expected = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][0])
        self._test_base_url_helper(expected, self.filters)

    def test_base_url_with_non_existent_service(self):
        self.filters = {
            'service': 'BAD_SERVICE',
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self._test_base_url_helper, None, self.filters)

    def test_base_url_without_service(self):
        self.filters = {
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion'
        }
        self.assertRaises(exceptions.EndpointNotFound,
                          self._test_base_url_helper, None, self.filters)

    def test_base_url_with_api_version_filter(self):
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion',
            'api_version': 'v12'
        }
        expected = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][1], replacement='v12')
        self._test_base_url_helper(expected, self.filters)

    def test_base_url_with_skip_path_filter(self):
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'publicURL',
            'region': 'FakeRegion',
            'skip_path': True
        }
        expected = 'http://fake_url/'
        self._test_base_url_helper(expected, self.filters)

    def test_token_not_expired(self):
        expiry_data = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        auth_data = self._auth_data_with_expiry(
            expiry_data.strftime(self.auth_provider.EXPIRY_DATE_FORMAT))
        self.assertFalse(self.auth_provider.is_expired(auth_data))

    def test_token_expired(self):
        expiry_data = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        auth_data = self._auth_data_with_expiry(
            expiry_data.strftime(self.auth_provider.EXPIRY_DATE_FORMAT))
        self.assertTrue(self.auth_provider.is_expired(auth_data))

    def test_token_not_expired_to_be_renewed(self):
        expiry_data = datetime.datetime.utcnow() + \
            self.auth_provider.token_expiry_threshold / 2
        auth_data = self._auth_data_with_expiry(
            expiry_data.strftime(self.auth_provider.EXPIRY_DATE_FORMAT))
        self.assertTrue(self.auth_provider.is_expired(auth_data))


class TestKeystoneV3AuthProvider(TestKeystoneV2AuthProvider):
    _endpoints = fake_identity.IDENTITY_V3_RESPONSE['token']['catalog']
    _auth_provider_class = auth.KeystoneV3AuthProvider
    credentials = fake_credentials.FakeKeystoneV3Credentials()

    def setUp(self):
        super(TestKeystoneV3AuthProvider, self).setUp()
        self.stubs.Set(v3_client.V3TokenClientJSON, 'raw_request',
                       fake_identity._fake_v3_response)

    def _get_fake_alt_identity(self):
        return fake_identity.ALT_IDENTITY_V3['token']

    def _get_result_url_from_endpoint(self, ep, replacement=None):
        if replacement:
            return ep['url'].replace('v3', replacement)
        return ep['url']

    def _auth_data_with_expiry(self, date_as_string):
        token, access = self.auth_provider.auth_data
        access['expires_at'] = date_as_string
        return token, access

    def _get_from_fake_identity(self, attr):
        token = fake_identity.IDENTITY_V3_RESPONSE['token']
        if attr == 'user_id':
            return token['user']['id']
        elif attr == 'project_id':
            return token['project']['id']
        elif attr == 'user_domain_id':
            return token['user']['domain']['id']
        elif attr == 'project_domain_id':
            return token['project']['domain']['id']

    def test_check_credentials_missing_attribute(self):
        # reset credentials to fresh ones
        self.credentials.reset()
        for attr in ['username', 'password', 'user_domain_name',
                     'project_domain_name']:
            cred = copy.copy(self.credentials)
            del cred[attr]
            self.assertFalse(self.auth_provider.check_credentials(cred),
                             "Credentials should be invalid without %s" % attr)

    def test_check_domain_credentials_missing_attribute(self):
        # reset credentials to fresh ones
        self.credentials.reset()
        domain_creds = fake_credentials.FakeKeystoneV3DomainCredentials()
        for attr in ['username', 'password', 'user_domain_name']:
            cred = copy.copy(domain_creds)
            del cred[attr]
            self.assertFalse(self.auth_provider.check_credentials(cred),
                             "Credentials should be invalid without %s" % attr)

    def test_fill_credentials(self):
        self.auth_provider.fill_credentials()
        creds = self.auth_provider.credentials
        for attr in ['user_id', 'project_id', 'user_domain_id',
                     'project_domain_id']:
            self.assertEqual(self._get_from_fake_identity(attr),
                             getattr(creds, attr))

    # Overwrites v2 test
    def test_base_url_to_get_admin_endpoint(self):
        self.filters = {
            'service': 'compute',
            'endpoint_type': 'admin',
            'region': 'MiddleEarthRegion'
        }
        expected = self._get_result_url_from_endpoint(
            self._endpoints[0]['endpoints'][2])
        self._test_base_url_helper(expected, self.filters)
