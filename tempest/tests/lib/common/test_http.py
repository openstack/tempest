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

import urllib3

from tempest.lib.common import http
from tempest.tests import base


CERT_NONE = 'CERT_NONE'
CERT_REQUIRED = 'CERT_REQUIRED'
CERT_LOCATION = '/etc/ssl/certs/ca-certificates.crt'
PROXY_URL = 'http://myproxy:3128'
REQUEST_URL = 'http://10.0.0.107:5000/v2.0'
REQUEST_METHOD = 'GET'


class TestClosingHttp(base.TestCase):

    def closing_http(self, **kwargs):
        return http.ClosingHttp(**kwargs)

    def test_closing_http(self):
        connection = self.closing_http()

        self.assertNotIn('cert_reqs', connection.connection_pool_kw)
        self.assertNotIn('ca_certs', connection.connection_pool_kw)
        self.assertNotIn('timeout', connection.connection_pool_kw)

    def test_closing_http_with_ca_certs(self):
        connection = self.closing_http(ca_certs=CERT_LOCATION)

        self.assertEqual(CERT_REQUIRED,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertEqual(CERT_LOCATION,
                         connection.connection_pool_kw['ca_certs'])

    def test_closing_http_with_dscv(self):
        connection = self.closing_http(
            disable_ssl_certificate_validation=True)

        self.assertEqual(CERT_NONE,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertNotIn('ca_certs',
                         connection.connection_pool_kw)

    def test_closing_http_with_ca_certs_and_dscv(self):
        connection = self.closing_http(
            disable_ssl_certificate_validation=True,
            ca_certs=CERT_LOCATION)

        self.assertEqual(CERT_NONE,
                         connection.connection_pool_kw['cert_reqs'])
        self.assertNotIn('ca_certs',
                         connection.connection_pool_kw)

    def test_closing_http_with_timeout(self):
        timeout = 30
        connection = self.closing_http(timeout=timeout)
        self.assertEqual(timeout,
                         connection.connection_pool_kw['timeout'])

    def test_request(self):
        # Given
        connection = self.closing_http()
        http_response = urllib3.HTTPResponse()
        request = self.patch('urllib3.PoolManager.request',
                             return_value=http_response)
        retry = self.patch('urllib3.util.Retry')

        # When
        response, data = connection.request(
            method=REQUEST_METHOD,
            url=REQUEST_URL)

        # Then
        request.assert_called_once_with(
            REQUEST_METHOD,
            REQUEST_URL,
            headers={'connection': 'close'},
            retries=retry(raise_on_redirect=False, redirect=5))
        self.assertEqual(
            {'content-location': REQUEST_URL,
             'status': str(http_response.status)},
            response)
        self.assertEqual(http_response.status, response.status)
        self.assertEqual(http_response.reason, response.reason)
        self.assertEqual(http_response.version, response.version)
        self.assertEqual(http_response.data, data)

    def test_request_with_fields(self):
        # Given
        connection = self.closing_http()
        http_response = urllib3.HTTPResponse()
        request = self.patch('urllib3.PoolManager.request',
                             return_value=http_response)
        retry = self.patch('urllib3.util.Retry')
        fields = object()

        # When
        connection.request(
            method=REQUEST_METHOD,
            url=REQUEST_URL,
            fields=fields)

        # Then
        request.assert_called_once_with(
            REQUEST_METHOD,
            REQUEST_URL,
            fields=fields,
            headers=dict(connection='close'),
            retries=retry(raise_on_redirect=False, redirect=5))

    def test_request_with_headers(self):
        # Given
        connection = self.closing_http()
        headers = {'Xtra Key': 'Xtra Value'}
        http_response = urllib3.HTTPResponse(headers=headers)
        request = self.patch('urllib3.PoolManager.request',
                             return_value=http_response)
        retry = self.patch('urllib3.util.Retry')

        # When
        response, _ = connection.request(
            method=REQUEST_METHOD,
            url=REQUEST_URL,
            headers=headers)

        # Then
        request.assert_called_once_with(
            REQUEST_METHOD,
            REQUEST_URL,
            headers=dict(headers, connection='close'),
            retries=retry(raise_on_redirect=False, redirect=5))
        self.assertEqual(
            {'content-location': REQUEST_URL,
             'status': str(http_response.status),
             'xtra key': 'Xtra Value'},
            response)


class TestClosingProxyHttp(TestClosingHttp):

    def closing_http(self, proxy_url=PROXY_URL, **kwargs):
        connection = http.ClosingProxyHttp(proxy_url=proxy_url, **kwargs)
        self.assertHasProxy(connection, proxy_url)
        return connection

    def test_class_without_proxy_url(self):
        self.assertRaises(ValueError, http.ClosingProxyHttp, None)

    def assertHasProxy(self, connection, proxy_url):
        self.assertIsInstance(connection, http.ClosingProxyHttp)
        proxy = connection.proxy
        self.assertEqual(proxy_url,
                         '%s://%s:%i' % (proxy.scheme,
                                         proxy.host,
                                         proxy.port))


class TestClosingHttpRedirects(base.TestCase):
    def test_redirect_default(self):
        connection = http.ClosingHttp()
        self.assertTrue(connection.follow_redirects)

    def test_redirect_off(self):
        connection = http.ClosingHttp(follow_redirects=False)
        self.assertFalse(connection.follow_redirects)


class TestClosingProxyHttpRedirects(base.TestCase):
    def test_redirect_default(self):
        connection = http.ClosingProxyHttp(proxy_url=PROXY_URL)
        self.assertTrue(connection.follow_redirects)

    def test_redirect_off(self):
        connection = http.ClosingProxyHttp(follow_redirects=False,
                                           proxy_url=PROXY_URL)
        self.assertFalse(connection.follow_redirects)
