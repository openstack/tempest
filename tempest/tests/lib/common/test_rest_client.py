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

import copy

import fixtures
import jsonschema
from oslo_serialization import jsonutils as json
import six

from tempest.lib.common import http
from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.tests import base
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_http
import tempest.tests.utils as utils


class BaseRestClientTestClass(base.TestCase):

    url = 'fake_endpoint'

    def setUp(self):
        super(BaseRestClientTestClass, self).setUp()
        self.fake_auth_provider = fake_auth_provider.FakeAuthProvider()
        self.rest_client = rest_client.RestClient(
            self.fake_auth_provider, None, None)
        self.patchobject(http.ClosingHttp, 'request', self.fake_http.request)
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
                                                 '_log_request'))


class TestRestClientHTTPMethods(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientHTTPMethods, self).setUp()
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
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
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
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

    def _verify_headers(self, resp):
        resp = dict((k.lower(), v) for k, v in six.iteritems(resp))
        self.assertEqual(self.header_value, resp['accept'])
        self.assertEqual(self.header_value, resp['content-type'])

    def setUp(self):
        super(TestRestClientHeadersJSON, self).setUp()
        self.header_value = 'application/json'

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
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
                                                 'response_checker'))
        resp, __ = self.rest_client.head(self.url)
        self._verify_headers(resp)

    def test_copy(self):
        resp, __ = self.rest_client.copy(self.url)
        self._verify_headers(resp)


class TestRestClientUpdateHeaders(BaseRestClientTestClass):
    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientUpdateHeaders, self).setUp()
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
                                                 '_error_checker'))
        self.headers = {'X-Configuration-Session': 'session_id'}

    def test_post_update_headers(self):
        __, return_dict = self.rest_client.post(self.url, {},
                                                extra_headers=True,
                                                headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_get_update_headers(self):
        __, return_dict = self.rest_client.get(self.url,
                                               extra_headers=True,
                                               headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_delete_update_headers(self):
        __, return_dict = self.rest_client.delete(self.url,
                                                  extra_headers=True,
                                                  headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_patch_update_headers(self):
        __, return_dict = self.rest_client.patch(self.url, {},
                                                 extra_headers=True,
                                                 headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_put_update_headers(self):
        __, return_dict = self.rest_client.put(self.url, {},
                                               extra_headers=True,
                                               headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_head_update_headers(self):
        self.useFixture(fixtures.MockPatchObject(self.rest_client,
                                                 'response_checker'))

        __, return_dict = self.rest_client.head(self.url,
                                                extra_headers=True,
                                                headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )

    def test_copy_update_headers(self):
        __, return_dict = self.rest_client.copy(self.url,
                                                extra_headers=True,
                                                headers=self.headers)

        self.assertDictContainsSubset(
            {'X-Configuration-Session': 'session_id',
             'Content-Type': 'application/json',
             'Accept': 'application/json'},
            return_dict['headers']
        )


class TestRestClientParseRespJSON(BaseRestClientTestClass):
    TYPE = "json"

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
    null_dict = {}

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRestClientParseRespJSON, self).setUp()
        self.rest_client.TYPE = self.TYPE

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

    def test_parse_nullable_dict(self):
        body = self.rest_client._parse_resp(json.dumps(self.null_dict))
        self.assertEqual(self.null_dict, body)

    def test_parse_empty_list(self):
        empty_list = []
        body = self.rest_client._parse_resp(json.dumps(empty_list))
        self.assertEqual(empty_list, body)


class TestRestClientErrorCheckerJSON(base.TestCase):
    c_type = "application/json"

    def set_data(self, r_code, enc=None, r_body=None, absolute_limit=True):
        if enc is None:
            enc = self.c_type
        resp_dict = {'status': r_code, 'content-type': enc}
        resp_body = {'resp_body': 'fake_resp_body'}

        if absolute_limit is False:
            resp_dict.update({'retry-after': 120})
            resp_body.update({'overLimit': {'message': 'fake_message'}})
        resp = fake_http.fake_http_response(headers=resp_dict,
                                            status=int(r_code),
                                            body=json.dumps(resp_body))
        data = {
            "resp": resp,
            "resp_body": json.dumps(resp_body)
        }
        if r_body is not None:
            data.update({"resp_body": r_body})
        return data

    def setUp(self):
        super(TestRestClientErrorCheckerJSON, self).setUp()
        self.rest_client = rest_client.RestClient(
            fake_auth_provider.FakeAuthProvider(), None, None)

    def test_response_less_than_400(self):
        self.rest_client._error_checker(**self.set_data("399"))

    def _test_error_checker(self, exception_type, data):
        e = self.assertRaises(exception_type,
                              self.rest_client._error_checker,
                              **data)
        self.assertEqual(e.resp, data['resp'])
        self.assertTrue(hasattr(e, 'resp_body'))
        return e

    def test_response_400(self):
        self._test_error_checker(exceptions.BadRequest, self.set_data("400"))

    def test_response_401(self):
        self._test_error_checker(exceptions.Unauthorized, self.set_data("401"))

    def test_response_403(self):
        self._test_error_checker(exceptions.Forbidden, self.set_data("403"))

    def test_response_404(self):
        self._test_error_checker(exceptions.NotFound, self.set_data("404"))

    def test_response_409(self):
        self._test_error_checker(exceptions.Conflict, self.set_data("409"))

    def test_response_410(self):
        self._test_error_checker(exceptions.Gone, self.set_data("410"))

    def test_response_412(self):
        self._test_error_checker(exceptions.PreconditionFailed,
                                 self.set_data("412"))

    def test_response_413(self):
        self._test_error_checker(exceptions.OverLimit, self.set_data("413"))

    def test_response_413_without_absolute_limit(self):
        self._test_error_checker(exceptions.RateLimitExceeded,
                                 self.set_data("413", absolute_limit=False))

    def test_response_415(self):
        self._test_error_checker(exceptions.InvalidContentType,
                                 self.set_data("415"))

    def test_response_422(self):
        self._test_error_checker(exceptions.UnprocessableEntity,
                                 self.set_data("422"))

    def test_response_500_with_text(self):
        # _parse_resp is expected to return 'str'
        self._test_error_checker(exceptions.ServerFault, self.set_data("500"))

    def test_response_501_with_text(self):
        self._test_error_checker(exceptions.NotImplemented,
                                 self.set_data("501"))

    def test_response_400_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.BadRequest,
                                     self.set_data("400", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_401_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.Unauthorized,
                                     self.set_data("401", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_403_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.Forbidden,
                                     self.set_data("403", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_404_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.NotFound,
                                     self.set_data("404", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_404_with_invalid_dict(self):
        r_body = '{"foo": "bar"]'
        e = self._test_error_checker(exceptions.NotFound,
                                     self.set_data("404", r_body=r_body))

        expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_410_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.Gone,
                                     self.set_data("410", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_410_with_invalid_dict(self):
        r_body = '{"foo": "bar"]'
        e = self._test_error_checker(exceptions.Gone,
                                     self.set_data("410", r_body=r_body))

        expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_409_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.Conflict,
                                     self.set_data("409", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_500_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        e = self._test_error_checker(exceptions.ServerFault,
                                     self.set_data("500", r_body=r_body))

        if self.c_type == 'application/json':
            expected = {"err": "fake_resp_body"}
        else:
            expected = r_body
        self.assertEqual(expected, e.resp_body)

    def test_response_501_with_dict(self):
        r_body = '{"resp_body": {"err": "fake_resp_body"}}'
        self._test_error_checker(exceptions.NotImplemented,
                                 self.set_data("501", r_body=r_body))

    def test_response_bigger_than_400(self):
        # Any response code, that bigger than 400, and not in
        # (401, 403, 404, 409, 412, 413, 422, 500, 501)
        self._test_error_checker(exceptions.UnexpectedResponseCode,
                                 self.set_data("402"))


class TestRestClientErrorCheckerTEXT(TestRestClientErrorCheckerJSON):
    c_type = "text/plain"

    def test_fake_content_type(self):
        # This test is required only in one exemplar
        # Any response code, that bigger than 400, and not in
        # (401, 403, 404, 409, 413, 422, 500, 501)
        self._test_error_checker(exceptions.UnexpectedContentType,
                                 self.set_data("405", enc="fake_enc"))

    def test_response_413_without_absolute_limit(self):
        # Skip this test because rest_client cannot get overLimit message
        # from text body.
        pass


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
        timeout = 1
        self.rest_client.build_timeout = timeout

        time_mock = self.patch('time.time')
        time_mock.side_effect = utils.generate_timeout_series(timeout)

        self.assertRaises(exceptions.TimeoutException,
                          self.rest_client.wait_for_resource_deletion,
                          '1234')

        # time.time() should be called twice, first to start the timer
        # and then to compute the timedelta
        self.assertEqual(2, time_mock.call_count)

    def test_wait_for_deletion_with_unimplemented_deleted_method(self):
        self.rest_client.is_resource_deleted = self.original_deleted_method
        self.assertRaises(NotImplementedError,
                          self.rest_client.wait_for_resource_deletion,
                          '1234')

    def test_get_versions(self):
        self.rest_client._parse_resp = lambda x: [{'id': 'v1'}, {'id': 'v2'}]
        actual_resp, actual_versions = self.rest_client.get_versions()
        self.assertEqual(['v1', 'v2'], list(actual_versions))

    def test__str__(self):
        def get_token():
            return "deadbeef"

        self.fake_auth_provider.get_token = get_token
        self.assertIsNotNone(str(self.rest_client))


class TestRateLimiting(BaseRestClientTestClass):

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestRateLimiting, self).setUp()

    def test__get_retry_after_delay_with_integer(self):
        resp = {'retry-after': '123'}
        self.assertEqual(123, self.rest_client._get_retry_after_delay(resp))

    def test__get_retry_after_delay_with_http_date(self):
        resp = {
            'date': 'Mon, 4 Apr 2016 21:56:23 GMT',
            'retry-after': 'Mon, 4 Apr 2016 21:58:26 GMT',
        }
        self.assertEqual(123, self.rest_client._get_retry_after_delay(resp))

    def test__get_retry_after_delay_of_zero_with_integer(self):
        resp = {'retry-after': '0'}
        self.assertEqual(1, self.rest_client._get_retry_after_delay(resp))

    def test__get_retry_after_delay_of_zero_with_http_date(self):
        resp = {
            'date': 'Mon, 4 Apr 2016 21:56:23 GMT',
            'retry-after': 'Mon, 4 Apr 2016 21:56:23 GMT',
        }
        self.assertEqual(1, self.rest_client._get_retry_after_delay(resp))

    def test__get_retry_after_delay_with_missing_date_header(self):
        resp = {
            'retry-after': 'Mon, 4 Apr 2016 21:58:26 GMT',
        }
        self.assertRaises(ValueError, self.rest_client._get_retry_after_delay,
                          resp)

    def test__get_retry_after_delay_with_invalid_http_date(self):
        resp = {
            'retry-after': 'Mon, 4 AAA 2016 21:58:26 GMT',
            'date': 'Mon, 4 Apr 2016 21:56:23 GMT',
        }
        self.assertRaises(ValueError, self.rest_client._get_retry_after_delay,
                          resp)

    def test__get_retry_after_delay_with_missing_retry_after_header(self):
        self.assertRaises(ValueError, self.rest_client._get_retry_after_delay,
                          {})

    def test_is_absolute_limit_gives_false_with_retry_after(self):
        resp = {'retry-after': 123}

        # is_absolute_limit() requires the overLimit body to be unwrapped
        resp_body = self.rest_client._parse_resp("""{
            "overLimit": {
                "message": ""
            }
        }""")
        self.assertFalse(self.rest_client.is_absolute_limit(resp, resp_body))


class TestProperties(BaseRestClientTestClass):

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestProperties, self).setUp()
        creds_dict = {
            'username': 'test-user',
            'user_id': 'test-user_id',
            'tenant_name': 'test-tenant_name',
            'tenant_id': 'test-tenant_id',
            'password': 'test-password'
        }
        self.rest_client = rest_client.RestClient(
            fake_auth_provider.FakeAuthProvider(creds_dict=creds_dict),
            None, None)

    def test_properties(self):
        self.assertEqual('test-user', self.rest_client.user)
        self.assertEqual('test-user_id', self.rest_client.user_id)
        self.assertEqual('test-tenant_name', self.rest_client.tenant_name)
        self.assertEqual('test-tenant_id', self.rest_client.tenant_id)
        self.assertEqual('test-password', self.rest_client.password)

        self.rest_client.api_version = 'v1'
        expected = {'api_version': 'v1',
                    'endpoint_type': 'publicURL',
                    'region': None,
                    'name': None,
                    'service': None,
                    'skip_path': True}
        self.rest_client.skip_path()
        self.assertEqual(expected, self.rest_client.filters)

        self.rest_client.reset_path()
        self.rest_client.api_version = 'v1'
        expected = {'api_version': 'v1',
                    'endpoint_type': 'publicURL',
                    'region': None,
                    'name': None,
                    'service': None}
        self.assertEqual(expected, self.rest_client.filters)


class TestExpectedSuccess(BaseRestClientTestClass):

    def setUp(self):
        self.fake_http = fake_http.fake_httplib2()
        super(TestExpectedSuccess, self).setUp()

    def test_expected_succes_int_match(self):
        expected_code = 202
        read_code = 202
        resp = self.rest_client.expected_success(expected_code, read_code)
        # Assert None resp on success
        self.assertFalse(resp)

    def test_expected_succes_int_no_match(self):
        expected_code = 204
        read_code = 202
        self.assertRaises(exceptions.InvalidHttpSuccessCode,
                          self.rest_client.expected_success,
                          expected_code, read_code)

    def test_expected_succes_list_match(self):
        expected_code = [202, 204]
        read_code = 202
        resp = self.rest_client.expected_success(expected_code, read_code)
        # Assert None resp on success
        self.assertFalse(resp)

    def test_expected_succes_list_no_match(self):
        expected_code = [202, 204]
        read_code = 200
        self.assertRaises(exceptions.InvalidHttpSuccessCode,
                          self.rest_client.expected_success,
                          expected_code, read_code)

    def test_non_success_expected_int(self):
        expected_code = 404
        read_code = 202
        self.assertRaises(AssertionError, self.rest_client.expected_success,
                          expected_code, read_code)

    def test_non_success_expected_list(self):
        expected_code = [404, 202]
        read_code = 202
        self.assertRaises(AssertionError, self.rest_client.expected_success,
                          expected_code, read_code)

    def test_non_success_read_code_as_string(self):
        expected_code = 202
        read_code = '202'
        self.assertRaises(TypeError, self.rest_client.expected_success,
                          expected_code, read_code)

    def test_non_success_read_code_as_list(self):
        expected_code = 202
        read_code = [202]
        self.assertRaises(TypeError, self.rest_client.expected_success,
                          expected_code, read_code)

    def test_non_success_expected_code_as_non_int(self):
        expected_code = ['201', 202]
        read_code = 202
        self.assertRaises(AssertionError, self.rest_client.expected_success,
                          expected_code, read_code)


class TestResponseBody(base.TestCase):

    def test_str(self):
        response = {'status': 200}
        body = {'key1': 'value1'}
        actual = rest_client.ResponseBody(response, body)
        self.assertEqual("response: %s\nBody: %s" % (response, body),
                         str(actual))


class TestResponseBodyData(base.TestCase):

    def test_str(self):
        response = {'status': 200}
        data = 'data1'
        actual = rest_client.ResponseBodyData(response, data)
        self.assertEqual("response: %s\nBody: %s" % (response, data),
                         str(actual))


class TestResponseBodyList(base.TestCase):

    def test_str(self):
        response = {'status': 200}
        body = ['value1', 'value2', 'value3']
        actual = rest_client.ResponseBodyList(response, body)
        self.assertEqual("response: %s\nBody: %s" % (response, body),
                         str(actual))


class TestJSONSchemaValidationBase(base.TestCase):

    class Response(dict):

        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    def setUp(self):
        super(TestJSONSchemaValidationBase, self).setUp()
        self.fake_auth_provider = fake_auth_provider.FakeAuthProvider()
        self.rest_client = rest_client.RestClient(
            self.fake_auth_provider, None, None)

    def _test_validate_pass(self, schema, resp_body, status=200):
        resp = self.Response()
        resp.status = status
        self.rest_client.validate_response(schema, resp, resp_body)

    def _test_validate_fail(self, schema, resp_body, status=200,
                            error_msg="HTTP response body is invalid"):
        resp = self.Response()
        resp.status = status
        ex = self.assertRaises(exceptions.InvalidHTTPResponseBody,
                               self.rest_client.validate_response,
                               schema, resp, resp_body)
        self.assertIn(error_msg, ex._error_string)


class TestRestClientJSONSchemaValidation(TestJSONSchemaValidationBase):

    schema = {
        'status_code': [200],
        'response_body': {
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'integer',
                },
            },
            'required': ['foo']
        }
    }

    def test_validate_pass_with_http_success_code(self):
        body = {'foo': 12}
        self._test_validate_pass(self.schema, body, status=200)

    def test_validate_pass_with_http_redirect_code(self):
        body = {'foo': 12}
        schema = copy.deepcopy(self.schema)
        schema['status_code'] = 300
        self._test_validate_pass(schema, body, status=300)

    def test_validate_not_http_success_code(self):
        schema = {
            'status_code': [200]
        }
        body = {}
        self._test_validate_pass(schema, body, status=400)

    def test_validate_multiple_allowed_type(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': ['integer', 'string'],
                    },
                },
                'required': ['foo']
            }
        }
        body = {'foo': 12}
        self._test_validate_pass(schema, body)
        body = {'foo': '12'}
        self._test_validate_pass(schema, body)

    def test_validate_enable_additional_property_pass(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'integer'}
                },
                'additionalProperties': True,
                'required': ['foo']
            }
        }
        body = {'foo': 12, 'foo2': 'foo2value'}
        self._test_validate_pass(schema, body)

    def test_validate_disable_additional_property_pass(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'integer'}
                },
                'additionalProperties': False,
                'required': ['foo']
            }
        }
        body = {'foo': 12}
        self._test_validate_pass(schema, body)

    def test_validate_disable_additional_property_fail(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {'type': 'integer'}
                },
                'additionalProperties': False,
                'required': ['foo']
            }
        }
        body = {'foo': 12, 'foo2': 'foo2value'}
        self._test_validate_fail(schema, body)

    def test_validate_wrong_status_code(self):
        schema = {
            'status_code': [202]
        }
        body = {}
        resp = self.Response()
        resp.status = 200
        ex = self.assertRaises(exceptions.InvalidHttpSuccessCode,
                               self.rest_client.validate_response,
                               schema, resp, body)
        self.assertIn("Unexpected http success status code", ex._error_string)

    def test_validate_wrong_attribute_type(self):
        body = {'foo': 1.2}
        self._test_validate_fail(self.schema, body)

    def test_validate_unexpected_response_body(self):
        schema = {
            'status_code': [200],
        }
        body = {'foo': 12}
        self._test_validate_fail(
            schema, body,
            error_msg="HTTP response body should not exist")

    def test_validate_missing_response_body(self):
        body = {}
        self._test_validate_fail(self.schema, body)

    def test_validate_missing_required_attribute(self):
        body = {'notfoo': 12}
        self._test_validate_fail(self.schema, body)

    def test_validate_response_body_not_list(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'list_items': {
                        'type': 'array',
                        'items': {'foo': {'type': 'integer'}}
                    }
                },
                'required': ['list_items'],
            }
        }
        body = {'foo': 12}
        self._test_validate_fail(schema, body)

    def test_validate_response_body_list_pass(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'list_items': {
                        'type': 'array',
                        'items': {'foo': {'type': 'integer'}}
                    }
                },
                'required': ['list_items'],
            }
        }
        body = {'list_items': [{'foo': 12}, {'foo': 10}]}
        self._test_validate_pass(schema, body)


class TestRestClientJSONHeaderSchemaValidation(TestJSONSchemaValidationBase):

    schema = {
        'status_code': [200],
        'response_header': {
            'type': 'object',
            'properties': {
                'foo': {'type': 'integer'}
            },
            'required': ['foo']
        }
    }

    def test_validate_header_schema_pass(self):
        resp_body = {}
        resp = self.Response()
        resp.status = 200
        resp.foo = 12
        self.rest_client.validate_response(self.schema, resp, resp_body)

    def test_validate_header_schema_fail(self):
        resp_body = {}
        resp = self.Response()
        resp.status = 200
        resp.foo = 1.2
        ex = self.assertRaises(exceptions.InvalidHTTPResponseHeader,
                               self.rest_client.validate_response,
                               self.schema, resp, resp_body)
        self.assertIn("HTTP response header is invalid", ex._error_string)


class TestRestClientJSONSchemaFormatValidation(TestJSONSchemaValidationBase):

    schema = {
        'status_code': [200],
        'response_body': {
            'type': 'object',
            'properties': {
                'foo': {
                    'type': 'string',
                    'format': 'email'
                }
            },
            'required': ['foo']
        }
    }

    def test_validate_format_pass(self):
        body = {'foo': 'example@example.com'}
        self._test_validate_pass(self.schema, body)

    def test_validate_format_fail(self):
        body = {'foo': 'wrong_email'}
        self._test_validate_fail(self.schema, body)

    def test_validate_formats_in_oneOf_pass(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'oneOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': '10.0.0.0'}
        self._test_validate_pass(schema, body)
        body = {'foo': 'FE80:0000:0000:0000:0202:B3FF:FE1E:8329'}
        self._test_validate_pass(schema, body)

    def test_validate_formats_in_oneOf_fail_both_match(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'oneOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv4'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': '10.0.0.0'}
        self._test_validate_fail(schema, body)

    def test_validate_formats_in_oneOf_fail_no_match(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'oneOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': 'wrong_ip_format'}
        self._test_validate_fail(schema, body)

    def test_validate_formats_in_anyOf_pass(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'anyOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': '10.0.0.0'}
        self._test_validate_pass(schema, body)
        body = {'foo': 'FE80:0000:0000:0000:0202:B3FF:FE1E:8329'}
        self._test_validate_pass(schema, body)

    def test_validate_formats_in_anyOf_pass_both_match(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'anyOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv4'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': '10.0.0.0'}
        self._test_validate_pass(schema, body)

    def test_validate_formats_in_anyOf_fail_no_match(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'anyOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': 'wrong_ip_format'}
        self._test_validate_fail(schema, body)

    def test_validate_formats_pass_for_unknow_format(self):
        schema = {
            'status_code': [200],
            'response_body': {
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'string',
                        'format': 'UNKNOWN'
                    }
                },
                'required': ['foo']
            }
        }
        body = {'foo': 'example@example.com'}
        self._test_validate_pass(schema, body)


class TestRestClientJSONSchemaValidatorVersion(TestJSONSchemaValidationBase):

    schema = {
        'status_code': [200],
        'response_body': {
            'type': 'object',
            'properties': {
                'foo': {'type': 'string'}
            }
        }
    }

    def test_current_json_schema_validator_version(self):
        with fixtures.MockPatchObject(jsonschema.Draft4Validator,
                                      "check_schema") as chk_schema:
            body = {'foo': 'test'}
            self._test_validate_pass(self.schema, body)
            chk_schema.mock.assert_called_once_with(
                self.schema['response_body'])
