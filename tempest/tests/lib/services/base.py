# Copyright 2015 Deutsche Telekom AG.  All rights reserved.
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

import fixtures
from oslo_serialization import jsonutils as json

from tempest.tests import base
from tempest.tests.lib import fake_http


class BaseServiceTest(base.TestCase):
    def create_response(self, body, to_utf=False, status=200, headers=None):
        json_body = {}
        if body:
            json_body = json.dumps(body)
            if to_utf:
                json_body = json_body.encode('utf-8')
        resp = fake_http.fake_http_response(headers, status=status), json_body
        return resp

    def check_service_client_function(self, function, function2mock,
                                      body, to_utf=False, status=200,
                                      headers=None, mock_args=None,
                                      resp_as_string=False,
                                      **kwargs):
        """Mock a service client function for unit testing.

        :param function: The service client function to call.
        :param function2mock: The REST call to mock inside the service client
               function.
        :param body: Expected response body returned by the service client
               function.
        :param to_utf: Whether to use UTF-8 encoding for response.
        :param status: Expected response status returned by the service client
               function.
        :param headers: Expected headers returned by the service client
               function.
        :param mock_args: List/dict/value of expected args/kwargs called by
               function2mock. For example:
               * If mock_args=['foo'] then ``assert_called_once_with('foo')``
                 is called.
               * If mock_args={'foo': 'bar'} then
                 ``assert_called_once_with(foo='bar')`` is called.
               * If mock_args='foo' then ``assert_called_once_with('foo')``
                 is called.
        :param resp_as_string: Whether response body is retruned as string.
               This is for service client methods which return ResponseBodyData
               object.
        :param kwargs: kwargs that are passed to function.
        """
        mocked_response = self.create_response(body, to_utf, status, headers)
        fixture = self.useFixture(fixtures.MockPatch(
            function2mock, return_value=mocked_response))
        if kwargs:
            resp = function(**kwargs)
        else:
            resp = function()
        if resp_as_string:
            resp = resp.data
        self.assertEqual(body, resp)
        if isinstance(mock_args, list):
            fixture.mock.assert_called_once_with(*mock_args)
        elif isinstance(mock_args, dict):
            fixture.mock.assert_called_once_with(**mock_args)
        elif mock_args is not None:
            fixture.mock.assert_called_once_with(mock_args)
