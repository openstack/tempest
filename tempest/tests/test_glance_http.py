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

import httplib
import json
import socket

import mock
from oslotest import mockpatch
import six
from tempest_lib import exceptions as lib_exc

from tempest.common import glance_http
from tempest import exceptions
from tempest.tests import base
from tempest.tests import fake_auth_provider
from tempest.tests import fake_http


class TestGlanceHTTPClient(base.TestCase):

    def setUp(self):
        super(TestGlanceHTTPClient, self).setUp()
        self.fake_http = fake_http.fake_httplib2(return_type=200)
        # NOTE(maurosr): using http here implies that we will be using httplib
        # directly. With https glance_client would use an httpS version, but
        # the real backend would still be httplib anyway and since we mock it
        # that there is no reason to care.
        self.endpoint = 'http://fake_url.com'
        self.fake_auth = fake_auth_provider.FakeAuthProvider()

        self.fake_auth.base_url = mock.MagicMock(return_value=self.endpoint)

        self.useFixture(mockpatch.PatchObject(
            httplib.HTTPConnection,
            'request',
            side_effect=self.fake_http.request(self.endpoint)[1]))
        self.client = glance_http.HTTPClient(self.fake_auth, {})

    def _set_response_fixture(self, header, status, resp_body):
        resp = fake_http.fake_httplib(header, status=status,
                                      body=six.StringIO(resp_body))
        self.useFixture(mockpatch.PatchObject(httplib.HTTPConnection,
                        'getresponse', return_value=resp))
        return resp

    def test_json_request_without_content_type_header_in_response(self):
        self._set_response_fixture({}, 200, 'fake_response_body')
        self.assertRaises(lib_exc.InvalidContentType,
                          self.client.json_request, 'GET', '/images')

    def test_json_request_with_xml_content_type_header_in_request(self):
        self.assertRaises(lib_exc.InvalidContentType,
                          self.client.json_request, 'GET', '/images',
                          headers={'Content-Type': 'application/xml'})

    def test_json_request_with_xml_content_type_header_in_response(self):
        self._set_response_fixture({'content-type': 'application/xml'},
                                   200, 'fake_response_body')
        self.assertRaises(lib_exc.InvalidContentType,
                          self.client.json_request, 'GET', '/images')

    def test_json_request_with_json_content_type_header_only_in_resp(self):
        self._set_response_fixture({'content-type': 'application/json'},
                                   200, 'fake_response_body')
        resp, body = self.client.json_request('GET', '/images')
        self.assertEqual(200, resp.status)
        self.assertEqual('fake_response_body', body)

    def test_json_request_with_json_content_type_header_in_req_and_resp(self):
        self._set_response_fixture({'content-type': 'application/json'},
                                   200, 'fake_response_body')
        resp, body = self.client.json_request('GET', '/images', headers={
            'Content-Type': 'application/json'})
        self.assertEqual(200, resp.status)
        self.assertEqual('fake_response_body', body)

    def test_json_request_fails_to_json_loads(self):
        self._set_response_fixture({'content-type': 'application/json'},
                                   200, 'fake_response_body')
        self.useFixture(mockpatch.PatchObject(json, 'loads',
                        side_effect=ValueError()))
        resp, body = self.client.json_request('GET', '/images')
        self.assertEqual(200, resp.status)
        self.assertEqual(body, 'fake_response_body')

    def test_json_request_socket_timeout(self):
        self.useFixture(mockpatch.PatchObject(httplib.HTTPConnection,
                                              'request',
                                              side_effect=socket.timeout()))
        self.assertRaises(exceptions.TimeoutException,
                          self.client.json_request, 'GET', '/images')

    def test_json_request_endpoint_not_found(self):
        self.useFixture(mockpatch.PatchObject(httplib.HTTPConnection,
                                              'request',
                                              side_effect=socket.gaierror()))
        self.assertRaises(exceptions.EndpointNotFound,
                          self.client.json_request, 'GET', '/images')

    def test_raw_request(self):
        self._set_response_fixture({}, 200, 'fake_response_body')
        resp, body = self.client.raw_request('GET', '/images')
        self.assertEqual(200, resp.status)
        self.assertEqual('fake_response_body', body.read())

    def test_raw_request_with_response_chunked(self):
        self._set_response_fixture({}, 200, 'fake_response_body')
        self.useFixture(mockpatch.PatchObject(glance_http,
                                              'CHUNKSIZE', 1))
        resp, body = self.client.raw_request('GET', '/images')
        self.assertEqual(200, resp.status)
        self.assertEqual('fake_response_body', body.read())

    def test_raw_request_chunked(self):
        self.useFixture(mockpatch.PatchObject(glance_http,
                                              'CHUNKSIZE', 1))
        self.useFixture(mockpatch.PatchObject(httplib.HTTPConnection,
                        'endheaders'))
        self.useFixture(mockpatch.PatchObject(httplib.HTTPConnection,
                        'send'))

        self._set_response_fixture({}, 200, 'fake_response_body')
        req_body = six.StringIO('fake_request_body')
        resp, body = self.client.raw_request('PUT', '/images', body=req_body)
        self.assertEqual(200, resp.status)
        self.assertEqual('fake_response_body', body.read())
        httplib.HTTPConnection.send.assert_call_count(req_body.len)

    def test_get_connection_class_for_https(self):
        conn_class = self.client.get_connection_class('https')
        self.assertEqual(glance_http.VerifiedHTTPSConnection, conn_class)

    def test_get_connection_class_for_http(self):
        conn_class = (self.client.get_connection_class('http'))
        self.assertEqual(httplib.HTTPConnection, conn_class)

    def test_get_connection_http(self):
        self.assertTrue(isinstance(self.client.get_connection(),
                                   httplib.HTTPConnection))

    def test_get_connection_https(self):
        endpoint = 'https://fake_url.com'
        self.fake_auth.base_url = mock.MagicMock(return_value=endpoint)
        self.client = glance_http.HTTPClient(self.fake_auth, {})
        self.assertTrue(isinstance(self.client.get_connection(),
                                   glance_http.VerifiedHTTPSConnection))

    def test_get_connection_url_not_fount(self):
        self.useFixture(mockpatch.PatchObject(self.client, 'connection_class',
                                              side_effect=httplib.InvalidURL()
                                              ))
        self.assertRaises(exceptions.EndpointNotFound,
                          self.client.get_connection)

    def test_get_connection_kwargs_default_for_http(self):
        kwargs = self.client.get_connection_kwargs('http')
        self.assertEqual(600, kwargs['timeout'])
        self.assertEqual(1, len(kwargs.keys()))

    def test_get_connection_kwargs_set_timeout_for_http(self):
        kwargs = self.client.get_connection_kwargs('http', timeout=10,
                                                   ca_certs='foo')
        self.assertEqual(10, kwargs['timeout'])
        # nothing more than timeout is evaluated for http connections
        self.assertEqual(1, len(kwargs.keys()))

    def test_get_connection_kwargs_default_for_https(self):
        kwargs = self.client.get_connection_kwargs('https')
        self.assertEqual(600, kwargs['timeout'])
        self.assertEqual(None, kwargs['ca_certs'])
        self.assertEqual(None, kwargs['cert_file'])
        self.assertEqual(None, kwargs['key_file'])
        self.assertEqual(False, kwargs['insecure'])
        self.assertEqual(True, kwargs['ssl_compression'])
        self.assertEqual(6, len(kwargs.keys()))

    def test_get_connection_kwargs_set_params_for_https(self):
        kwargs = self.client.get_connection_kwargs('https', timeout=10,
                                                   ca_certs='foo',
                                                   cert_file='/foo/bar.cert',
                                                   key_file='/foo/key.pem',
                                                   insecure=True,
                                                   ssl_compression=False)
        self.assertEqual(10, kwargs['timeout'])
        self.assertEqual('foo', kwargs['ca_certs'])
        self.assertEqual('/foo/bar.cert', kwargs['cert_file'])
        self.assertEqual('/foo/key.pem', kwargs['key_file'])
        self.assertEqual(True, kwargs['insecure'])
        self.assertEqual(False, kwargs['ssl_compression'])
        self.assertEqual(6, len(kwargs.keys()))


class TestResponseBodyIterator(base.TestCase):

    def test_iter_default_chunk_size_64k(self):
        resp = fake_http.fake_httplib({}, six.StringIO(
            'X' * (glance_http.CHUNKSIZE + 1)))
        iterator = glance_http.ResponseBodyIterator(resp)
        chunks = list(iterator)
        self.assertEqual(chunks, ['X' * glance_http.CHUNKSIZE, 'X'])
