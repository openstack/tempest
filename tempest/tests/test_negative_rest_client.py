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

import mock
from oslotest import mockpatch

from tempest.common import negative_rest_client
from tempest import config
from tempest.tests import base
from tempest.tests import fake_auth_provider
from tempest.tests import fake_config


class TestNegativeRestClient(base.TestCase):

    url = 'fake_endpoint'

    def setUp(self):
        super(TestNegativeRestClient, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.patchobject(config, 'TempestConfigPrivate',
                         fake_config.FakePrivate)
        self.negative_rest_client = negative_rest_client.NegativeRestClient(
            fake_auth_provider.FakeAuthProvider(), None)
        self.useFixture(mockpatch.PatchObject(self.negative_rest_client,
                                              '_log_request'))

    @mock.patch('tempest.lib.common.rest_client.RestClient.post',
                return_value=(mock.Mock(), mock.Mock()))
    def test_post(self, mock_post):
        __, return_dict = self.negative_rest_client.send_request('POST',
                                                                 self.url,
                                                                 [], {})
        mock_post.assert_called_once_with(self.url, {})

    @mock.patch('tempest.lib.common.rest_client.RestClient.get',
                return_value=(mock.Mock(), mock.Mock()))
    def test_get(self, mock_get):
        __, return_dict = self.negative_rest_client.send_request('GET',
                                                                 self.url,
                                                                 [])
        mock_get.assert_called_once_with(self.url)

    @mock.patch('tempest.lib.common.rest_client.RestClient.delete',
                return_value=(mock.Mock(), mock.Mock()))
    def test_delete(self, mock_delete):
        __, return_dict = self.negative_rest_client.send_request('DELETE',
                                                                 self.url,
                                                                 [])
        mock_delete.assert_called_once_with(self.url)

    @mock.patch('tempest.lib.common.rest_client.RestClient.patch',
                return_value=(mock.Mock(), mock.Mock()))
    def test_patch(self, mock_patch):
        __, return_dict = self.negative_rest_client.send_request('PATCH',
                                                                 self.url,
                                                                 [], {})
        mock_patch.assert_called_once_with(self.url, {})

    @mock.patch('tempest.lib.common.rest_client.RestClient.put',
                return_value=(mock.Mock(), mock.Mock()))
    def test_put(self, mock_put):
        __, return_dict = self.negative_rest_client.send_request('PUT',
                                                                 self.url,
                                                                 [], {})
        mock_put.assert_called_once_with(self.url, {})

    @mock.patch('tempest.lib.common.rest_client.RestClient.head',
                return_value=(mock.Mock(), mock.Mock()))
    def test_head(self, mock_head):
        __, return_dict = self.negative_rest_client.send_request('HEAD',
                                                                 self.url,
                                                                 [])
        mock_head.assert_called_once_with(self.url)

    @mock.patch('tempest.lib.common.rest_client.RestClient.copy',
                return_value=(mock.Mock(), mock.Mock()))
    def test_copy(self, mock_copy):
        __, return_dict = self.negative_rest_client.send_request('COPY',
                                                                 self.url,
                                                                 [])
        mock_copy.assert_called_once_with(self.url)

    def test_other(self):
        self.assertRaises(AssertionError,
                          self.negative_rest_client.send_request,
                          'OTHER', self.url, [])
