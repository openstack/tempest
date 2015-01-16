# (c) 2015 Deutsche Telekom AG
# Copyright 2015 Red Hat, Inc.
# Copyright 2015 NEC Corporation
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

import httplib2
from oslotest import mockpatch

from tempest.common import negative_rest_client
from tempest import config
from tempest.tests import base
from tempest.tests import fake_auth_provider
from tempest.tests import fake_config
from tempest.tests import fake_http


class TestNegativeRestClient(base.TestCase):

    url = 'fake_endpoint'

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestNegativeRestClient, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.stubs.Set(httplib2.Http, 'request', self.fake_http.request)
        self.negative_rest_client = negative_rest_client.NegativeRestClient(
            fake_auth_provider.FakeAuthProvider(), None)
        self.useFixture(mockpatch.PatchObject(self.negative_rest_client,
                                              '_log_request'))

    def test_post(self):
        __, return_dict = self.negative_rest_client.send_request('POST',
                                                                 self.url,
                                                                 [], {})
        self.assertEqual('POST', return_dict['method'])

    def test_get(self):
        __, return_dict = self.negative_rest_client.send_request('GET',
                                                                 self.url,
                                                                 [])
        self.assertEqual('GET', return_dict['method'])

    def test_delete(self):
        __, return_dict = self.negative_rest_client.send_request('DELETE',
                                                                 self.url,
                                                                 [])
        self.assertEqual('DELETE', return_dict['method'])

    def test_patch(self):
        __, return_dict = self.negative_rest_client.send_request('PATCH',
                                                                 self.url,
                                                                 [], {})
        self.assertEqual('PATCH', return_dict['method'])

    def test_put(self):
        __, return_dict = self.negative_rest_client.send_request('PUT',
                                                                 self.url,
                                                                 [], {})
        self.assertEqual('PUT', return_dict['method'])

    def test_head(self):
        self.useFixture(mockpatch.PatchObject(self.negative_rest_client,
                                              'response_checker'))
        __, return_dict = self.negative_rest_client.send_request('HEAD',
                                                                 self.url,
                                                                 [])
        self.assertEqual('HEAD', return_dict['method'])

    def test_copy(self):
        __, return_dict = self.negative_rest_client.send_request('COPY',
                                                                 self.url,
                                                                 [])
        self.assertEqual('COPY', return_dict['method'])

    def test_other(self):
        self.assertRaises(AssertionError,
                          self.negative_rest_client.send_request,
                          'OTHER', self.url, [])
