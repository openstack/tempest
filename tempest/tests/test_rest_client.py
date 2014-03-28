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
import json

from tempest.common import rest_client
from tempest.common import xml_utils as xml
from tempest import config
from tempest import exceptions
from tempest.openstack.common.fixture import mockpatch
from tempest.tests import base
from tempest.tests import fake_auth_provider
from tempest.tests import fake_config
from tempest.tests import fake_http


class BaseRestClientTestClass(base.TestCase):

    url = 'fake_endpoint'

    def _get_region(self):
        return 'fake region'

    def setUp(self):
        super(BaseRestClientTestClass, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.rest_client = rest_client.RestClient(
            fake_auth_provider.FakeAuthProvider())
        self.stubs.Set(httplib2.Http, 'request', self.fake_http.request)
        self.useFixture(mockpatch.PatchObject(self.rest_client, '_get_region',
                                              side_effect=self._get_region()))
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              '_log_request'))


class TestRestClientHTTPMethods(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientHTTPMethods, self).setUp()
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              '_error_checker'))

    def test_post(self):
        __, return_dict = self.rest_client.post(self.url, {}, {})
        self.assertEqual('POST', return_dict['method'])

    def test_get(self):
        __, return_dict = self.rest_client.get(self.url)
        self.assertEqual('GET', return_dict['method'])

    def test_delete(self):
        __, return_dict = self.rest_client.delete(self.url)
        self.assertEqual('DELETE', return_dict['method'])

    def test_patch(self):
        __, return_dict = self.rest_client.patch(self.url, {}, {})
        self.assertEqual('PATCH', return_dict['method'])

    def test_put(self):
        __, return_dict = self.rest_client.put(self.url, {}, {})
        self.assertEqual('PUT', return_dict['method'])

    def test_head(self):
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              'response_checker'))
        __, return_dict = self.rest_client.head(self.url)
        self.assertEqual('HEAD', return_dict['method'])

    def test_copy(self):
        __, return_dict = self.rest_client.copy(self.url)
        self.assertEqual('COPY', return_dict['method'])


class TestRestClientNotFoundHandling(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2(404)
        super(TestRestClientNotFoundHandling, self).setUp()

    def test_post(self):
        self.assertRaises(exceptions.NotFound, self.rest_client.post,
                          self.url, {}, {})


class TestRestClientHeadersJSON(TestRestClientHTTPMethods):
    TYPE = "json"

    def _verify_headers(self, resp):
        self.assertEqual(self.rest_client._get_type(), self.TYPE)
        resp = dict((k.lower(), v) for k, v in resp.iteritems())
        self.assertEqual(self.header_value, resp['accept'])
        self.assertEqual(self.header_value, resp['content-type'])

    def setUp(self):
        super(TestRestClientHeadersJSON, self).setUp()
        self.rest_client.TYPE = self.TYPE
        self.header_value = 'application/%s' % self.rest_client._get_type()

    def test_post(self):
        resp, __ = self.rest_client.post(self.url, {})
        self._verify_headers(resp)

    def test_get(self):
        resp, __ = self.rest_client.get(self.url)
        self._verify_headers(resp)

    def test_delete(self):
        resp, __ = self.rest_client.delete(self.url)
        self._verify_headers(resp)

    def test_patch(self):
        resp, __ = self.rest_client.patch(self.url, {})
        self._verify_headers(resp)

    def test_put(self):
        resp, __ = self.rest_client.put(self.url, {})
        self._verify_headers(resp)

    def test_head(self):
        self.useFixture(mockpatch.PatchObject(self.rest_client,
                                              'response_checker'))
        resp, __ = self.rest_client.head(self.url)
        self._verify_headers(resp)

    def test_copy(self):
        resp, __ = self.rest_client.copy(self.url)
        self._verify_headers(resp)


class TestRestClientHeadersXML(TestRestClientHeadersJSON):
    TYPE = "xml"

    # These two tests are needed in one exemplar
    def test_send_json_accept_xml(self):
        resp, __ = self.rest_client.get(self.url,
                                        self.rest_client.get_headers("xml",
                                                                     "json"))
        resp = dict((k.lower(), v) for k, v in resp.iteritems())
        self.assertEqual("application/json", resp["content-type"])
        self.assertEqual("application/xml", resp["accept"])

    def test_send_xml_accept_json(self):
        resp, __ = self.rest_client.get(self.url,
                                        self.rest_client.get_headers("json",
                                                                     "xml"))
        resp = dict((k.lower(), v) for k, v in resp.iteritems())
        self.assertEqual("application/json", resp["accept"])
        self.assertEqual("application/xml", resp["content-type"])


class TestRestClientParseRespXML(BaseRestClientTestClass):
    TYPE = "xml"

    keys = ["fake_key1", "fake_key2"]
    values = ["fake_value1", "fake_value2"]
    item_expected = dict((key, value) for (key, value) in zip(keys, values))
    list_expected = {"body_list": [
        {keys[0]: values[0]},
        {keys[1]: values[1]},
    ]}
    dict_expected = {"body_dict": {
        keys[0]: values[0],
        keys[1]: values[1],
    }}

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientParseRespXML, self).setUp()
        self.rest_client.TYPE = self.TYPE

    def test_parse_resp_body_item(self):
        body_item = xml.Element("item", **self.item_expected)
        body = self.rest_client._parse_resp(str(xml.Document(body_item)))
        self.assertEqual(self.item_expected, body)

    def test_parse_resp_body_list(self):
        self.rest_client.list_tags = ["fake_list", ]
        body_list = xml.Element(self.rest_client.list_tags[0])
        for i in range(2):
            body_list.append(xml.Element("fake_item",
                                         **self.list_expected["body_list"][i]))
        body = self.rest_client._parse_resp(str(xml.Document(body_list)))
        self.assertEqual(self.list_expected["body_list"], body)

    def test_parse_resp_body_dict(self):
        self.rest_client.dict_tags = ["fake_dict", ]
        body_dict = xml.Element(self.rest_client.dict_tags[0])

        for i in range(2):
            body_dict.append(xml.Element("fake_item", xml.Text(self.values[i]),
                                         key=self.keys[i]))

        body = self.rest_client._parse_resp(str(xml.Document(body_dict)))
        self.assertEqual(self.dict_expected["body_dict"], body)


class TestRestClientParseRespJSON(TestRestClientParseRespXML):
    TYPE = "json"

    def test_parse_resp_body_item(self):
        body = self.rest_client._parse_resp(json.dumps(self.item_expected))
        self.assertEqual(self.item_expected, body)

    def test_parse_resp_body_list(self):
        body = self.rest_client._parse_resp(json.dumps(self.list_expected))
        self.assertEqual(self.list_expected["body_list"], body)

    def test_parse_resp_body_dict(self):
        body = self.rest_client._parse_resp(json.dumps(self.dict_expected))
        self.assertEqual(self.dict_expected["body_dict"], body)

    def test_parse_resp_two_top_keys(self):
        dict_two_keys = self.dict_expected.copy()
        dict_two_keys.update({"second_key": ""})
        body = self.rest_client._parse_resp(json.dumps(dict_two_keys))
        self.assertEqual(dict_two_keys, body)

    def test_parse_resp_one_top_key_without_list_or_dict(self):
        data = {"one_top_key": "not_list_or_dict_value"}
        body = self.rest_client._parse_resp(json.dumps(data))
        self.assertEqual(data, body)


class TestRestClientErrorCheckerJSON(base.TestCase):
    c_type = "application/json"

    def set_data(self, r_code, enc=None, r_body=None):
        if enc is None:
            enc = self.c_type
        resp_dict = {'status': r_code, 'content-type': enc}
        resp = httplib2.Response(resp_dict)
        data = {
            "method": "fake_method",
            "url": "fake_url",
            "headers": "fake_headers",
            "body": "fake_body",
            "resp": resp,
            "resp_body": '{"resp_body": "fake_resp_body"}',
        }
        if r_body is not None:
            data.update({"resp_body": r_body})
        return data

    def setUp(self):
        super(TestRestClientErrorCheckerJSON, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        self.stubs.Set(config, 'TempestConfigPrivate', fake_config.FakePrivate)
        self.rest_client = rest_client.RestClient(
            fake_auth_provider.FakeAuthProvider())

    def test_response_less_than_400(self):
        self.rest_client._error_checker(**self.set_data("399"))

    def test_response_400(self):
        self.assertRaises(exceptions.BadRequest,
                          self.rest_client._error_checker,
                          **self.set_data("400"))

    def test_response_401(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.rest_client._error_checker,
                          **self.set_data("401"))

    def test_response_403(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.rest_client._error_checker,
                          **self.set_data("403"))

    def test_response_404(self):
        self.assertRaises(exceptions.NotFound,
                          self.rest_client._error_checker,
                          **self.set_data("404"))

    def test_response_409(self):
        self.assertRaises(exceptions.Conflict,
                          self.rest_client._error_checker,
                          **self.set_data("409"))

    def test_response_413(self):
        self.assertRaises(exceptions.OverLimit,
                          self.rest_client._error_checker,
                          **self.set_data("413"))

    def test_response_422(self):
        self.assertRaises(exceptions.UnprocessableEntity,
                          self.rest_client._error_checker,
                          **self.set_data("422"))

    def test_response_500_with_text(self):
        # _parse_resp is expected to return 'str'
        self.assertRaises(exceptions.ServerFault,
                          self.rest_client._error_checker,
                          **self.set_data("500"))

    def test_response_501_with_text(self):
        self.assertRaises(exceptions.ServerFault,
                          self.rest_client._error_checker,
                          **self.set_data("501"))

    def test_response_500_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        self.assertRaises(exceptions.ServerFault,
                          self.rest_client._error_checker,
                          **self.set_data("500", r_body=r_body))

    def test_response_501_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        self.assertRaises(exceptions.ServerFault,
                          self.rest_client._error_checker,
                          **self.set_data("501", r_body=r_body))

    def test_response_bigger_than_400(self):
        # Any response code, that bigger than 400, and not in
        # (401, 403, 404, 409, 413, 422, 500, 501)
        self.assertRaises(exceptions.UnexpectedResponseCode,
                          self.rest_client._error_checker,
                          **self.set_data("402"))


class TestRestClientErrorCheckerXML(TestRestClientErrorCheckerJSON):
    c_type = "application/xml"


class TestRestClientErrorCheckerTEXT(TestRestClientErrorCheckerJSON):
    c_type = "text/plain"

    def test_fake_content_type(self):
        # This test is required only in one exemplar
        # Any response code, that bigger than 400, and not in
        # (401, 403, 404, 409, 413, 422, 500, 501)
        self.assertRaises(exceptions.InvalidContentType,
                          self.rest_client._error_checker,
                          **self.set_data("405", enc="fake_enc"))


class TestRestClientUtils(BaseRestClientTestClass):

    def _is_resource_deleted(self, resource_id):
        if not isinstance(self.retry_pass, int):
            return False
        if self.retry_count >= self.retry_pass:
            return True
        self.retry_count = self.retry_count + 1
        return False

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientUtils, self).setUp()
        self.retry_count = 0
        self.retry_pass = None
        self.original_deleted_method = self.rest_client.is_resource_deleted
        self.rest_client.is_resource_deleted = self._is_resource_deleted

    def test_wait_for_resource_deletion(self):
        self.retry_pass = 2
        # Ensure timeout long enough for loop execution to hit retry count
        self.rest_client.build_timeout = 500
        sleep_mock = self.patch('time.sleep')
        self.rest_client.wait_for_resource_deletion('1234')
        self.assertEqual(len(sleep_mock.mock_calls), 2)

    def test_wait_for_resource_deletion_not_deleted(self):
        self.patch('time.sleep')
        # Set timeout to be very quick to force exception faster
        self.rest_client.build_timeout = 1
        self.assertRaises(exceptions.TimeoutException,
                          self.rest_client.wait_for_resource_deletion,
                          '1234')

    def test_wait_for_deletion_with_unimplemented_deleted_method(self):
        self.rest_client.is_resource_deleted = self.original_deleted_method
        self.assertRaises(NotImplementedError,
                          self.rest_client.wait_for_resource_deletion,
                          '1234')


class TestNegativeRestClient(BaseRestClientTestClass):

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestNegativeRestClient, self).setUp()
        self.negative_rest_client = rest_client.NegativeRestClient(
            fake_auth_provider.FakeAuthProvider())
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
