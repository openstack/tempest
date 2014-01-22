# Copyright 2013 IBM Corp.
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

import httplib2

from tempest.common import rest_client
from tempest import exceptions
from tempest.openstack.common.fixture import mockpatch
from tempest.tests import base
from tempest.tests import fake_config
from tempest.tests import fake_http


class BaseRestClientTestClass(base.TestCase):

    def _set_token(self):
        self.rest_client.token = 'fake token'

    def setUp(self):
        super(BaseRestClientTestClass, self).setUp()
        self.rest_client = rest_client.RestClient(fake_config.FakeConfig(),
                                                  'fake_user', 'fake_pass',
                                                  'http://fake_url/v2.0')
        self.stubs.Set(httplib2.Http, 'request', self.fake_http.request)
        self.useFixture(mockpatch.PatchObject(self.rest_client, '_set_auth',
                                              side_effect=self._set_token()))
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              '_log_response'))


class TestRestClientHTTPMethods(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientHTTPMethods, self).setUp()
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              '_error_checker'))

    def test_post(self):
        __, return_dict = self.rest_client.post('fake_endpoint', {},
                                                {})
        self.assertEqual('POST', return_dict['method'])

    def test_get(self):
        __, return_dict = self.rest_client.get('fake_endpoint')
        self.assertEqual('GET', return_dict['method'])

    def test_delete(self):
        __, return_dict = self.rest_client.delete('fake_endpoint')
        self.assertEqual('DELETE', return_dict['method'])

    def test_patch(self):
        __, return_dict = self.rest_client.patch('fake_endpoint', {},
                                                 {})
        self.assertEqual('PATCH', return_dict['method'])

    def test_put(self):
        __, return_dict = self.rest_client.put('fake_endpoint', {},
                                               {})
        self.assertEqual('PUT', return_dict['method'])

    def test_head(self):
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              'response_checker'))
        __, return_dict = self.rest_client.head('fake_endpoint')
        self.assertEqual('HEAD', return_dict['method'])

    def test_copy(self):
        __, return_dict = self.rest_client.copy('fake_endpoint')
        self.assertEqual('COPY', return_dict['method'])


class TestRestClientNotFoundHandling(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2(404)
        super(TestRestClientNotFoundHandling, self).setUp()

    def test_post(self):
        self.assertRaises(exceptions.NotFound, self.rest_client.post,
                          'fake_endpoint', {}, {})
