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

import httplib2
from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.tests.lib import base


class BaseComputeServiceTest(base.TestCase):
    def create_response(self, body, to_utf=False, status=200, headers=None):
        json_body = {}
        if body:
            json_body = json.dumps(body)
            if to_utf:
                json_body = json_body.encode('utf-8')
        resp_dict = {'status': status}
        if headers:
            resp_dict.update(headers)
        response = (httplib2.Response(resp_dict), json_body)
        return response

    def check_service_client_function(self, function, function2mock,
                                      body, to_utf=False, status=200,
                                      headers=None, **kwargs):
        mocked_response = self.create_response(body, to_utf, status, headers)
        self.useFixture(mockpatch.Patch(
            function2mock, return_value=mocked_response))
        if kwargs:
            resp = function(**kwargs)
        else:
            resp = function()
        self.assertEqual(body, resp)
