# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types
from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.tests import base
from tempest.tests.lib import fake_http


class TestJSONSchemaDateTimeFormat(base.TestCase):
    date_time_schema = [
        {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'date-time': parameter_types.date_time
                }
            }
        },
        {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'date-time': parameter_types.date_time_or_null
                }
            }
        }
    ]

    def test_valid_date_time_format(self):
        valid_instances = ['2016-10-02T10:00:00-05:00',
                           '2016-10-02T10:00:00+09:00',
                           '2016-10-02T15:00:00Z',
                           '2016-10-02T15:00:00.05Z']
        resp = fake_http.fake_http_response('', status=200)
        for instance in valid_instances:
            body = {'date-time': instance}
            for schema in self.date_time_schema:
                rest_client.RestClient.validate_response(schema, resp, body)

    def test_invalid_date_time_format(self):
        invalid_instances = ['2016-10-02 T10:00:00-05:00',
                             '2016-10-02T 15:00:00',
                             '2016-10-02T15:00:00.05 Z',
                             '2016-10-02:15:00:00.05Z',
                             'T15:00:00.05Z',
                             '2016:10:02T15:00:00',
                             '2016-10-02T15-00-00',
                             '2016-10-02T15.05Z',
                             '09MAR2015 11:15',
                             '13 Oct 2015 05:55:36 GMT',
                             '']
        resp = fake_http.fake_http_response('', status=200)
        for instance in invalid_instances:
            body = {'date-time': instance}
            for schema in self.date_time_schema:
                self.assertRaises(exceptions.InvalidHTTPResponseBody,
                                  rest_client.RestClient.validate_response,
                                  schema, resp, body)

    def test_date_time_or_null_format(self):
        instance = None
        resp = fake_http.fake_http_response('', status=200)
        body = {'date-time': instance}
        rest_client.RestClient.validate_response(self.date_time_schema[1],
                                                 resp, body)
        self.assertRaises(exceptions.InvalidHTTPResponseBody,
                          rest_client.RestClient.validate_response,
                          self.date_time_schema[0], resp, body)
