# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

import collections
import logging as real_logging
import re
import time

import jsonschema
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
import six

from tempest.lib.common import http
from tempest.lib.common.utils import misc as misc_utils
from tempest.lib import exceptions

# redrive rate limited calls at most twice
MAX_RECURSION_DEPTH = 2

# All the successful HTTP status codes from RFC 7231 & 4918
HTTP_SUCCESS = (200, 201, 202, 203, 204, 205, 206, 207)

# All the redirection HTTP status codes from RFC 7231 & 4918
HTTP_REDIRECTION = (300, 301, 302, 303, 304, 305, 306, 307)

# JSON Schema validator and format checker used for JSON Schema validation
JSONSCHEMA_VALIDATOR = jsonschema.Draft4Validator
FORMAT_CHECKER = jsonschema.draft4_format_checker


class RestClient(object):
    """Unified OpenStack RestClient class

    This class is used for building openstack api clients on top of. It is
    intended to provide a base layer for wrapping outgoing http requests in
    keystone auth as well as providing response code checking and error
    handling.

    :param auth_provider: an auth provider object used to wrap requests in auth
    :param str service: The service name to use for the catalog lookup
    :param str region: The region to use for the catalog lookup
    :param str endpoint_type: The endpoint type to use for the catalog lookup
    :param int build_interval: Time in seconds between to status checks in
                               wait loops
    :param int build_timeout: Timeout in seconds to wait for a wait operation.
    :param bool disable_ssl_certificate_validation: Set to true to disable ssl
                                                    certificate validation
    :param str ca_certs: File containing the CA Bundle to use in verifying a
                         TLS server cert
    :param str trace_request: Regex to use for specifying logging the entirety
                              of the request and response payload
    """
    TYPE = "json"

    # The version of the API this client implements
    api_version = None

    LOG = logging.getLogger(__name__)

    def __init__(self, auth_provider, service, region,
                 endpoint_type='publicURL',
                 build_interval=1, build_timeout=60,
                 disable_ssl_certificate_validation=False, ca_certs=None,
                 trace_requests=''):
        self.auth_provider = auth_provider
        self.service = service
        self.region = region
        self.endpoint_type = endpoint_type
        self.build_interval = build_interval
        self.build_timeout = build_timeout
        self.trace_requests = trace_requests

        self._skip_path = False
        self.general_header_lc = set(('cache-control', 'connection',
                                      'date', 'pragma', 'trailer',
                                      'transfer-encoding', 'via',
                                      'warning'))
        self.response_header_lc = set(('accept-ranges', 'age', 'etag',
                                       'location', 'proxy-authenticate',
                                       'retry-after', 'server',
                                       'vary', 'www-authenticate'))
        dscv = disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv, ca_certs=ca_certs)

    def _get_type(self):
        return self.TYPE

    def get_headers(self, accept_type=None, send_type=None):
        """Return the default headers which will be used with outgoing requests

        :param str accept_type: The media type to use for the Accept header, if
                                one isn't provided the object var TYPE will be
                                used
        :param str send_type: The media-type to use for the Content-Type
                              header, if one isn't provided the object var
                              TYPE will be used
        :rtype: dict
        :return: The dictionary of headers which can be used in the headers
                 dict for outgoing request
        """
        if accept_type is None:
            accept_type = self._get_type()
        if send_type is None:
            send_type = self._get_type()
        return {'Content-Type': 'application/%s' % send_type,
                'Accept': 'application/%s' % accept_type}

    def __str__(self):
        STRING_LIMIT = 80
        str_format = ("service:%s, base_url:%s, "
                      "filters: %s, build_interval:%s, build_timeout:%s"
                      "\ntoken:%s..., \nheaders:%s...")
        return str_format % (self.service, self.base_url,
                             self.filters, self.build_interval,
                             self.build_timeout,
                             str(self.token)[0:STRING_LIMIT],
                             str(self.get_headers())[0:STRING_LIMIT])

    @property
    def user(self):
        """The username used for requests

        :rtype: string
        :return: The username being used for requests
        """

        return self.auth_provider.credentials.username

    @property
    def user_id(self):
        """The user_id used for requests

        :rtype: string
        :return: The user id being used for requests
        """
        return self.auth_provider.credentials.user_id

    @property
    def tenant_name(self):
        """The tenant/project being used for requests

        :rtype: string
        :return: The tenant/project name being used for requests
        """
        return self.auth_provider.credentials.tenant_name

    @property
    def tenant_id(self):
        """The tenant/project id being used for requests

        :rtype: string
        :return: The tenant/project id being used for requests
        """
        return self.auth_provider.credentials.tenant_id

    @property
    def password(self):
        """The password being used for requests

        :rtype: string
        :return: The password being used for requests
        """
        return self.auth_provider.credentials.password

    @property
    def base_url(self):
        return self.auth_provider.base_url(filters=self.filters)

    @property
    def token(self):
        return self.auth_provider.get_token()

    @property
    def filters(self):
        _filters = dict(
            service=self.service,
            endpoint_type=self.endpoint_type,
            region=self.region
        )
        if self.api_version is not None:
            _filters['api_version'] = self.api_version
        if self._skip_path:
            _filters['skip_path'] = self._skip_path
        return _filters

    def skip_path(self):
        """When set, ignore the path part of the base URL from the catalog"""
        self._skip_path = True

    def reset_path(self):
        """When reset, use the base URL from the catalog as-is"""
        self._skip_path = False

    @classmethod
    def expected_success(cls, expected_code, read_code):
        """Check expected success response code against the http response

        :param int expected_code: The response code that is expected.
                                  Optionally a list of integers can be used
                                  to specify multiple valid success codes
        :param int read_code: The response code which was returned in the
                              response
        :raises AssertionError: if the expected_code isn't a valid http success
                                response code
        :raises exceptions.InvalidHttpSuccessCode: if the read code isn't an
                                                   expected http success code
        """
        assert_msg = ("This function only allowed to use for HTTP status"
                      "codes which explicitly defined in the RFC 7231 & 4918."
                      "{0} is not a defined Success Code!"
                      ).format(expected_code)
        if isinstance(expected_code, list):
            for code in expected_code:
                assert code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg
        else:
            assert expected_code in HTTP_SUCCESS + HTTP_REDIRECTION, assert_msg

        # NOTE(afazekas): the http status code above 400 is processed by
        # the _error_checker method
        if read_code < 400:
            pattern = """Unexpected http success status code {0},
                         The expected status code is {1}"""
            if ((not isinstance(expected_code, list) and
                 (read_code != expected_code)) or
                (isinstance(expected_code, list) and
                 (read_code not in expected_code))):
                details = pattern.format(read_code, expected_code)
                raise exceptions.InvalidHttpSuccessCode(details)

    def post(self, url, body, headers=None, extra_headers=False):
        """Send a HTTP POST request using keystone auth

        :param str url: the relative url to send the post request to
        :param dict body: the request body
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('POST', url, extra_headers, headers, body)

    def get(self, url, headers=None, extra_headers=False):
        """Send a HTTP GET request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('GET', url, extra_headers, headers)

    def delete(self, url, headers=None, body=None, extra_headers=False):
        """Send a HTTP DELETE request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict headers: The headers to use for the request
        :param dict body: the request body
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('DELETE', url, extra_headers, headers, body)

    def patch(self, url, body, headers=None, extra_headers=False):
        """Send a HTTP PATCH request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict body: the request body
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('PATCH', url, extra_headers, headers, body)

    def put(self, url, body, headers=None, extra_headers=False):
        """Send a HTTP PUT request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict body: the request body
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('PUT', url, extra_headers, headers, body)

    def head(self, url, headers=None, extra_headers=False):
        """Send a HTTP HEAD request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('HEAD', url, extra_headers, headers)

    def copy(self, url, headers=None, extra_headers=False):
        """Send a HTTP COPY request using keystone service catalog and auth

        :param str url: the relative url to send the post request to
        :param dict headers: The headers to use for the request
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :rtype: tuple
        """
        return self.request('COPY', url, extra_headers, headers)

    def get_versions(self):
        """Get the versions on a endpoint from the keystone catalog

        This method will make a GET request on the baseurl from the keystone
        catalog to return a list of API versions. It is expected that a GET
        on the endpoint in the catalog will return a list of supported API
        versions.

        :return tuple with response headers and list of version numbers
        :rtype: tuple
        """
        resp, body = self.get('')
        body = self._parse_resp(body)
        versions = map(lambda x: x['id'], body)
        return resp, versions

    def _get_request_id(self, resp):
        for i in ('x-openstack-request-id', 'x-compute-request-id'):
            if i in resp:
                return resp[i]
        return ""

    def _safe_body(self, body, maxlen=4096):
        # convert a structure into a string safely
        try:
            text = six.text_type(body)
        except UnicodeDecodeError:
            # if this isn't actually text, return marker that
            return "<BinaryData: removed>"
        if len(text) > maxlen:
            return text[:maxlen]
        else:
            return text

    def _log_request_start(self, method, req_url, req_headers=None,
                           req_body=None):
        if req_headers is None:
            req_headers = {}
        caller_name = misc_utils.find_test_caller()
        if self.trace_requests and re.search(self.trace_requests, caller_name):
            self.LOG.debug('Starting Request (%s): %s %s' %
                           (caller_name, method, req_url))

    def _log_request_full(self, method, req_url, resp,
                          secs="", req_headers=None,
                          req_body=None, resp_body=None,
                          caller_name=None, extra=None):
        if 'X-Auth-Token' in req_headers:
            req_headers['X-Auth-Token'] = '<omitted>'
        log_fmt = """Request - Headers: %s
        Body: %s
    Response - Headers: %s
        Body: %s"""

        self.LOG.debug(
            log_fmt % (
                str(req_headers),
                self._safe_body(req_body),
                str(resp),
                self._safe_body(resp_body)),
            extra=extra)

    def _log_request(self, method, req_url, resp,
                     secs="", req_headers=None,
                     req_body=None, resp_body=None):
        if req_headers is None:
            req_headers = {}
        # if we have the request id, put it in the right part of the log
        extra = dict(request_id=self._get_request_id(resp))
        # NOTE(sdague): while we still have 6 callers to this function
        # we're going to just provide work around on who is actually
        # providing timings by gracefully adding no content if they don't.
        # Once we're down to 1 caller, clean this up.
        caller_name = misc_utils.find_test_caller()
        if secs:
            secs = " %.3fs" % secs
        self.LOG.info(
            'Request (%s): %s %s %s%s' % (
                caller_name,
                resp['status'],
                method,
                req_url,
                secs),
            extra=extra)

        # Also look everything at DEBUG if you want to filter this
        # out, don't run at debug.
        if self.LOG.isEnabledFor(real_logging.DEBUG):
            self._log_request_full(method, req_url, resp, secs, req_headers,
                                   req_body, resp_body, caller_name, extra)

    def _parse_resp(self, body):
        try:
            body = json.loads(body)
        except ValueError:
            return body

        # We assume, that if the first value of the deserialized body's
        # item set is a dict or a list, that we just return the first value
        # of deserialized body.
        # Essentially "cutting out" the first placeholder element in a body
        # that looks like this:
        #
        #  {
        #    "users": [
        #      ...
        #    ]
        #  }
        try:
            # Ensure there are not more than one top-level keys
            # NOTE(freerunner): Ensure, that JSON is not nullable to
            # to prevent StopIteration Exception
            if len(body.keys()) != 1:
                return body
            # Just return the "wrapped" element
            first_key, first_item = six.next(six.iteritems(body))
            if isinstance(first_item, (dict, list)):
                return first_item
        except (ValueError, IndexError):
            pass
        return body

    def response_checker(self, method, resp, resp_body):
        """A sanity check on the response from a HTTP request

        This method does a sanity check on whether the response from an HTTP
        request conforms the HTTP RFC.

        :param str method: The HTTP verb of the request associated with the
                           response being passed in.
        :param resp: The response headers
        :param resp_body: The body of the response
        :raises ResponseWithNonEmptyBody: If the response with the status code
                                          is not supposed to have a body
        :raises ResponseWithEntity: If the response code is 205 but has an
                                    entity
        """
        if (resp.status in set((204, 205, 304)) or resp.status < 200 or
                method.upper() == 'HEAD') and resp_body:
            raise exceptions.ResponseWithNonEmptyBody(status=resp.status)
        # NOTE(afazekas):
        # If the HTTP Status Code is 205
        #   'The response MUST NOT include an entity.'
        # A HTTP entity has an entity-body and an 'entity-header'.
        # In the HTTP response specification (Section 6) the 'entity-header'
        # 'generic-header' and 'response-header' are in OR relation.
        # All headers not in the above two group are considered as entity
        # header in every interpretation.

        if (resp.status == 205 and
            0 != len(set(resp.keys()) - set(('status',)) -
                     self.response_header_lc - self.general_header_lc)):
                        raise exceptions.ResponseWithEntity()
        # NOTE(afazekas)
        # Now the swift sometimes (delete not empty container)
        # returns with non json error response, we can create new rest class
        # for swift.
        # Usually RFC2616 says error responses SHOULD contain an explanation.
        # The warning is normal for SHOULD/SHOULD NOT case

        # Likely it will cause an error
        if method != 'HEAD' and not resp_body and resp.status >= 400:
            self.LOG.warning("status >= 400 response with empty body")

    def _request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        # Authenticate the request with the auth provider
        req_url, req_headers, req_body = self.auth_provider.auth_request(
            method, url, headers, body, self.filters)

        # Do the actual request, and time it
        start = time.time()
        self._log_request_start(method, req_url)
        resp, resp_body = self.raw_request(
            req_url, method, headers=req_headers, body=req_body)
        end = time.time()
        self._log_request(method, req_url, resp, secs=(end - start),
                          req_headers=req_headers, req_body=req_body,
                          resp_body=resp_body)

        # Verify HTTP response codes
        self.response_checker(method, resp, resp_body)

        return resp, resp_body

    def raw_request(self, url, method, headers=None, body=None):
        """Send a raw HTTP request without the keystone catalog or auth

        This method sends a HTTP request in the same manner as the request()
        method, however it does so without using keystone auth or the catalog
        to determine the base url. Additionally no response handling is done
        the results from the request are just returned.

        :param str url: Full url to send the request
        :param str method: The HTTP verb to use for the request
        :param str headers: Headers to use for the request if none are specifed
                            the headers
        :param str body: Body to send with the request
        :rtype: tuple
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        """
        if headers is None:
            headers = self.get_headers()
        return self.http_obj.request(url, method,
                                     headers=headers, body=body)

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        """Send a HTTP request with keystone auth and using the catalog

        This method will send an HTTP request using keystone auth in the
        headers and the catalog to determine the endpoint to use for the
        baseurl to send the request to. Additionally

        When a response is received it will check it to see if an error
        response was received. If it was an exception will be raised to enable
        it to be handled quickly.

        This method will also handle rate-limiting, if a 413 response code is
        received it will retry the request after waiting the 'retry-after'
        duration from the header.

        :param str method: The HTTP verb to use for the request
        :param str url: Relative url to send the request to
        :param bool extra_headers: Boolean value than indicates if the headers
                                   returned by the get_headers() method are to
                                   be used but additional headers are needed in
                                   the request pass them in as a dict.
        :param dict headers: Headers to use for the request if none are
                             specifed the headers returned from the
                             get_headers() method are used. If the request
                             explicitly requires no headers use an empty dict.
        :param str body: Body to send with the request
        :rtype: tuple
        :return: a tuple with the first entry containing the response headers
                 and the second the response body
        :raises UnexpectedContentType: If the content-type of the response
                                       isn't an expect type
        :raises Unauthorized: If a 401 response code is received
        :raises Forbidden: If a 403 response code is received
        :raises NotFound: If a 404 response code is received
        :raises BadRequest: If a 400 response code is received
        :raises Gone: If a 410 response code is received
        :raises Conflict: If a 409 response code is received
        :raises OverLimit: If a 413 response code is received and over_limit is
                          not in the response body
        :raises RateLimitExceeded: If a 413 response code is received and
                                   over_limit is in the response body
        :raises InvalidContentType: If a 415 response code is received
        :raises UnprocessableEntity: If a 422 response code is received
        :raises InvalidHTTPResponseBody: The response body wasn't valid JSON
                                         and couldn't be parsed
        :raises NotImplemented: If a 501 response code is received
        :raises ServerFault: If a 500 response code is received
        :raises UnexpectedResponseCode: If a response code above 400 is
                                        received and it doesn't fall into any
                                        of the handled checks
        """
        # if extra_headers is True
        # default headers would be added to headers
        retry = 0

        if headers is None:
            # NOTE(vponomaryov): if some client do not need headers,
            # it should explicitly pass empty dict
            headers = self.get_headers()
        elif extra_headers:
            try:
                headers.update(self.get_headers())
            except (ValueError, TypeError):
                headers = self.get_headers()

        resp, resp_body = self._request(method, url,
                                        headers=headers, body=body)

        while (resp.status == 413 and
               'retry-after' in resp and
                not self.is_absolute_limit(
                    resp, self._parse_resp(resp_body)) and
                retry < MAX_RECURSION_DEPTH):
            retry += 1
            delay = int(resp['retry-after'])
            time.sleep(delay)
            resp, resp_body = self._request(method, url,
                                            headers=headers, body=body)
        self._error_checker(method, url, headers, body,
                            resp, resp_body)
        return resp, resp_body

    def _error_checker(self, method, url,
                       headers, body, resp, resp_body):

        # NOTE(mtreinish): Check for httplib response from glance_http. The
        # object can't be used here because importing httplib breaks httplib2.
        # If another object from a class not imported were passed here as
        # resp this could possibly fail
        if str(type(resp)) == "<type 'instance'>":
            ctype = resp.getheader('content-type')
        else:
            try:
                ctype = resp['content-type']
            # NOTE(mtreinish): Keystone delete user responses doesn't have a
            # content-type header. (They don't have a body) So just pretend it
            # is set.
            except KeyError:
                ctype = 'application/json'

        # It is not an error response
        if resp.status < 400:
            return

        JSON_ENC = ['application/json', 'application/json; charset=utf-8']
        # NOTE(mtreinish): This is for compatibility with Glance and swift
        # APIs. These are the return content types that Glance api v1
        # (and occasionally swift) are using.
        TXT_ENC = ['text/plain', 'text/html', 'text/html; charset=utf-8',
                   'text/plain; charset=utf-8']

        if ctype.lower() in JSON_ENC:
            parse_resp = True
        elif ctype.lower() in TXT_ENC:
            parse_resp = False
        else:
            raise exceptions.UnexpectedContentType(str(resp.status),
                                                   resp=resp)

        if resp.status == 401:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.Unauthorized(resp_body, resp=resp)

        if resp.status == 403:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.Forbidden(resp_body, resp=resp)

        if resp.status == 404:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.NotFound(resp_body, resp=resp)

        if resp.status == 400:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.BadRequest(resp_body, resp=resp)

        if resp.status == 410:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.Gone(resp_body, resp=resp)

        if resp.status == 409:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.Conflict(resp_body, resp=resp)

        if resp.status == 413:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            if self.is_absolute_limit(resp, resp_body):
                raise exceptions.OverLimit(resp_body, resp=resp)
            else:
                raise exceptions.RateLimitExceeded(resp_body, resp=resp)

        if resp.status == 415:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.InvalidContentType(resp_body, resp=resp)

        if resp.status == 422:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.UnprocessableEntity(resp_body, resp=resp)

        if resp.status in (500, 501):
            message = resp_body
            if parse_resp:
                try:
                    resp_body = self._parse_resp(resp_body)
                except ValueError:
                    # If response body is a non-json string message.
                    # Use resp_body as is and raise InvalidResponseBody
                    # exception.
                    raise exceptions.InvalidHTTPResponseBody(message)
                else:
                    if isinstance(resp_body, dict):
                        # I'm seeing both computeFault
                        # and cloudServersFault come back.
                        # Will file a bug to fix, but leave as is for now.
                        if 'cloudServersFault' in resp_body:
                            message = resp_body['cloudServersFault']['message']
                        elif 'computeFault' in resp_body:
                            message = resp_body['computeFault']['message']
                        elif 'error' in resp_body:
                            message = resp_body['error']['message']
                        elif 'message' in resp_body:
                            message = resp_body['message']
                    else:
                        message = resp_body

            if resp.status == 501:
                raise exceptions.NotImplemented(resp_body, resp=resp,
                                                message=message)
            else:
                raise exceptions.ServerFault(resp_body, resp=resp,
                                             message=message)

        if resp.status >= 400:
            raise exceptions.UnexpectedResponseCode(str(resp.status),
                                                    resp=resp)

    def is_absolute_limit(self, resp, resp_body):
        if (not isinstance(resp_body, collections.Mapping) or
                'retry-after' not in resp):
            return True
        over_limit = resp_body.get('overLimit', None)
        if not over_limit:
            return True
        return 'exceed' in over_limit.get('message', 'blabla')

    def wait_for_resource_deletion(self, id):
        """Waits for a resource to be deleted

        This method will loop over is_resource_deleted until either
        is_resource_deleted returns True or the build timeout is reached. This
        depends on is_resource_deleted being implemented

        :param str id: The id of the resource to check
        :raises TimeoutException: If the build_timeout has elapsed and the
                                  resource still hasn't been deleted
        """
        start_time = int(time.time())
        while True:
            if self.is_resource_deleted(id):
                return
            if int(time.time()) - start_time >= self.build_timeout:
                message = ('Failed to delete %(resource_type)s %(id)s within '
                           'the required time (%(timeout)s s).' %
                           {'resource_type': self.resource_type, 'id': id,
                            'timeout': self.build_timeout})
                caller = misc_utils.find_test_caller()
                if caller:
                    message = '(%s) %s' % (caller, message)
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)

    def is_resource_deleted(self, id):
        """Subclasses override with specific deletion detection."""
        message = ('"%s" does not implement is_resource_deleted'
                   % self.__class__.__name__)
        raise NotImplementedError(message)

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'resource'

    @classmethod
    def validate_response(cls, schema, resp, body):
        # Only check the response if the status code is a success code
        # TODO(cyeoh): Eventually we should be able to verify that a failure
        # code if it exists is something that we expect. This is explicitly
        # declared in the V3 API and so we should be able to export this in
        # the response schema. For now we'll ignore it.
        if resp.status in HTTP_SUCCESS + HTTP_REDIRECTION:
            cls.expected_success(schema['status_code'], resp.status)

            # Check the body of a response
            body_schema = schema.get('response_body')
            if body_schema:
                try:
                    jsonschema.validate(body, body_schema,
                                        cls=JSONSCHEMA_VALIDATOR,
                                        format_checker=FORMAT_CHECKER)
                except jsonschema.ValidationError as ex:
                    msg = ("HTTP response body is invalid (%s)") % ex
                    raise exceptions.InvalidHTTPResponseBody(msg)
            else:
                if body:
                    msg = ("HTTP response body should not exist (%s)") % body
                    raise exceptions.InvalidHTTPResponseBody(msg)

            # Check the header of a response
            header_schema = schema.get('response_header')
            if header_schema:
                try:
                    jsonschema.validate(resp, header_schema,
                                        cls=JSONSCHEMA_VALIDATOR,
                                        format_checker=FORMAT_CHECKER)
                except jsonschema.ValidationError as ex:
                    msg = ("HTTP response header is invalid (%s)") % ex
                    raise exceptions.InvalidHTTPResponseHeader(msg)


class ResponseBody(dict):
    """Class that wraps an http response and dict body into a single value.

    Callers that receive this object will normally use it as a dict but
    can extract the response if needed.
    """

    def __init__(self, response, body=None):
        body_data = body or {}
        self.update(body_data)
        self.response = response

    def __str__(self):
        body = super(ResponseBody, self).__str__()
        return "response: %s\nBody: %s" % (self.response, body)


class ResponseBodyData(object):
    """Class that wraps an http response and string data into a single value.

    """

    def __init__(self, response, data):
        self.response = response
        self.data = data

    def __str__(self):
        return "response: %s\nBody: %s" % (self.response, self.data)


class ResponseBodyList(list):
    """Class that wraps an http response and list body into a single value.

    Callers that receive this object will normally use it as a list but
    can extract the response if needed.
    """

    def __init__(self, response, body=None):
        body_data = body or []
        self.extend(body_data)
        self.response = response

    def __str__(self):
        body = super(ResponseBodyList, self).__str__()
        return "response: %s\nBody: %s" % (self.response, body)
