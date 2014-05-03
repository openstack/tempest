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
import inspect
import json
from lxml import etree
import re
import time

import jsonschema

from tempest.common import http
from tempest.common import xml_utils as common
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging

CONF = config.CONF

# redrive rate limited calls at most twice
MAX_RECURSION_DEPTH = 2
TOKEN_CHARS_RE = re.compile('^[-A-Za-z0-9+/=]*$')

# All the successful HTTP status codes from RFC 2616
HTTP_SUCCESS = (200, 201, 202, 203, 204, 205, 206)


class RestClient(object):

    TYPE = "json"

    # This is used by _parse_resp method
    # Redefine it for purposes of your xml service client
    # List should contain top-xml_tag-names of data, which is like list/array
    # For example, in keystone it is users, roles, tenants and services
    # All of it has children with same tag-names
    list_tags = []

    # This is used by _parse_resp method too
    # Used for selection of dict-like xmls,
    # like metadata for Vms in nova, and volumes in cinder
    dict_tags = ["metadata", ]

    LOG = logging.getLogger(__name__)

    def __init__(self, auth_provider):
        self.auth_provider = auth_provider

        self.endpoint_url = None
        self.service = None
        # The version of the API this client implements
        self.api_version = None
        self._skip_path = False
        self.build_interval = CONF.compute.build_interval
        self.build_timeout = CONF.compute.build_timeout
        self.general_header_lc = set(('cache-control', 'connection',
                                      'date', 'pragma', 'trailer',
                                      'transfer-encoding', 'via',
                                      'warning'))
        self.response_header_lc = set(('accept-ranges', 'age', 'etag',
                                       'location', 'proxy-authenticate',
                                       'retry-after', 'server',
                                       'vary', 'www-authenticate'))
        dscv = CONF.identity.disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv)

    def _get_type(self):
        return self.TYPE

    def get_headers(self, accept_type=None, send_type=None):
        if accept_type is None:
            accept_type = self._get_type()
        if send_type is None:
            send_type = self._get_type()
        return {'Content-Type': 'application/%s' % send_type,
                'Accept': 'application/%s' % accept_type}

    def __str__(self):
        STRING_LIMIT = 80
        str_format = ("config:%s, service:%s, base_url:%s, "
                      "filters: %s, build_interval:%s, build_timeout:%s"
                      "\ntoken:%s..., \nheaders:%s...")
        return str_format % (CONF, self.service, self.base_url,
                             self.filters, self.build_interval,
                             self.build_timeout,
                             str(self.token)[0:STRING_LIMIT],
                             str(self.get_headers())[0:STRING_LIMIT])

    def _get_region(self, service):
        """
        Returns the region for a specific service
        """
        service_region = None
        for cfgname in dir(CONF._config):
            # Find all config.FOO.catalog_type and assume FOO is a service.
            cfg = getattr(CONF, cfgname)
            catalog_type = getattr(cfg, 'catalog_type', None)
            if catalog_type == service:
                service_region = getattr(cfg, 'region', None)
        if not service_region:
            service_region = CONF.identity.region
        return service_region

    def _get_endpoint_type(self, service):
        """
        Returns the endpoint type for a specific service
        """
        # If the client requests a specific endpoint type, then be it
        if self.endpoint_url:
            return self.endpoint_url
        endpoint_type = None
        for cfgname in dir(CONF._config):
            # Find all config.FOO.catalog_type and assume FOO is a service.
            cfg = getattr(CONF, cfgname)
            catalog_type = getattr(cfg, 'catalog_type', None)
            if catalog_type == service:
                endpoint_type = getattr(cfg, 'endpoint_type', 'publicURL')
                break
        # Special case for compute v3 service which hasn't its own
        # configuration group
        else:
            if service == CONF.compute.catalog_v3_type:
                endpoint_type = CONF.compute.endpoint_type
        return endpoint_type

    @property
    def user(self):
        return self.auth_provider.credentials.get('username', None)

    @property
    def tenant_name(self):
        return self.auth_provider.credentials.get('tenant_name', None)

    @property
    def password(self):
        return self.auth_provider.credentials.get('password', None)

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
            endpoint_type=self._get_endpoint_type(self.service),
            region=self._get_region(self.service)
        )
        if self.api_version is not None:
            _filters['api_version'] = self.api_version
        if self._skip_path:
            _filters['skip_path'] = self._skip_path
        return _filters

    def skip_path(self):
        """
        When set, ignore the path part of the base URL from the catalog
        """
        self._skip_path = True

    def reset_path(self):
        """
        When reset, use the base URL from the catalog as-is
        """
        self._skip_path = False

    def expected_success(self, expected_code, read_code):
        assert_msg = ("This function only allowed to use for HTTP status"
                      "codes which explicitly defined in the RFC 2616. {0}"
                      " is not a defined Success Code!").format(expected_code)
        assert expected_code in HTTP_SUCCESS, assert_msg

        # NOTE(afazekas): the http status code above 400 is processed by
        # the _error_checker method
        if read_code < 400 and read_code != expected_code:
                pattern = """Unexpected http success status code {0},
                             The expected status code is {1}"""
                details = pattern.format(read_code, expected_code)
                raise exceptions.InvalidHttpSuccessCode(details)

    def post(self, url, body, headers=None, extra_headers=False):
        return self.request('POST', url, extra_headers, headers, body)

    def get(self, url, headers=None, extra_headers=False):
        return self.request('GET', url, extra_headers, headers)

    def delete(self, url, headers=None, body=None, extra_headers=False):
        return self.request('DELETE', url, extra_headers, headers, body)

    def patch(self, url, body, headers=None, extra_headers=False):
        return self.request('PATCH', url, extra_headers, headers, body)

    def put(self, url, body, headers=None, extra_headers=False):
        return self.request('PUT', url, extra_headers, headers, body)

    def head(self, url, headers=None, extra_headers=False):
        return self.request('HEAD', url, extra_headers, headers)

    def copy(self, url, headers=None, extra_headers=False):
        return self.request('COPY', url, extra_headers, headers)

    def get_versions(self):
        resp, body = self.get('')
        body = self._parse_resp(body)
        versions = map(lambda x: x['id'], body)
        return resp, versions

    def _find_caller(self):
        """Find the caller class and test name.

        Because we know that the interesting things that call us are
        test_* methods, and various kinds of setUp / tearDown, we
        can look through the call stack to find appropriate methods,
        and the class we were in when those were called.
        """
        caller_name = None
        names = []
        frame = inspect.currentframe()
        is_cleanup = False
        # Start climbing the ladder until we hit a good method
        while True:
            try:
                frame = frame.f_back
                name = frame.f_code.co_name
                names.append(name)
                if re.search("^(test_|setUp|tearDown)", name):
                    cname = ""
                    if 'self' in frame.f_locals:
                        cname = frame.f_locals['self'].__class__.__name__
                    if 'cls' in frame.f_locals:
                        cname = frame.f_locals['cls'].__name__
                    caller_name = cname + ":" + name
                    break
                elif re.search("^_run_cleanup", name):
                    is_cleanup = True
                else:
                    cname = ""
                    if 'self' in frame.f_locals:
                        cname = frame.f_locals['self'].__class__.__name__
                    if 'cls' in frame.f_locals:
                        cname = frame.f_locals['cls'].__name__

                    # the fact that we are running cleanups is indicated pretty
                    # deep in the stack, so if we see that we want to just
                    # start looking for a real class name, and declare victory
                    # once we do.
                    if is_cleanup and cname:
                        if not re.search("^RunTest", cname):
                            caller_name = cname + ":_run_cleanups"
                            break
            except Exception:
                break
        # prevents frame leaks
        del frame
        if caller_name is None:
            self.LOG.debug("Sane call name not found in %s" % names)
        return caller_name

    def _get_request_id(self, resp):
        for i in ('x-openstack-request-id', 'x-compute-request-id'):
            if i in resp:
                return resp[i]
        return ""

    def _log_request(self, method, req_url, resp,
                     secs="", req_headers={},
                     req_body=None, resp_body=None):
        # if we have the request id, put it in the right part of the log
        extra = dict(request_id=self._get_request_id(resp))
        # NOTE(sdague): while we still have 6 callers to this function
        # we're going to just provide work around on who is actually
        # providing timings by gracefully adding no content if they don't.
        # Once we're down to 1 caller, clean this up.
        caller_name = self._find_caller()
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

        # We intentionally duplicate the info content because in a parallel
        # world this is important to match
        trace_regex = CONF.debug.trace_requests
        if trace_regex and re.search(trace_regex, caller_name):
            if 'X-Auth-Token' in req_headers:
                req_headers['X-Auth-Token'] = '<omitted>'
            log_fmt = """Request (%s): %s %s %s%s
    Request - Headers: %s
        Body: %s
    Response - Headers: %s
        Body: %s"""

            self.LOG.debug(
                log_fmt % (
                    caller_name,
                    resp['status'],
                    method,
                    req_url,
                    secs,
                    str(req_headers),
                    str(req_body)[:2048],
                    str(resp),
                    str(resp_body)[:2048]),
                extra=extra)

    def _parse_resp(self, body):
        if self._get_type() is "json":
            body = json.loads(body)

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
                if len(body.keys()) > 1:
                    return body
                # Just return the "wrapped" element
                first_key, first_item = body.items()[0]
                if isinstance(first_item, (dict, list)):
                    return first_item
            except (ValueError, IndexError):
                pass
            return body
        elif self._get_type() is "xml":
            element = etree.fromstring(body)
            if any(s in element.tag for s in self.dict_tags):
                # Parse dictionary-like xmls (metadata, etc)
                dictionary = {}
                for el in element.getchildren():
                    dictionary[u"%s" % el.get("key")] = u"%s" % el.text
                return dictionary
            if any(s in element.tag for s in self.list_tags):
                # Parse list-like xmls (users, roles, etc)
                array = []
                for child in element.getchildren():
                    array.append(common.xml_to_json(child))
                return array

            # Parse one-item-like xmls (user, role, etc)
            return common.xml_to_json(element)

    def response_checker(self, method, url, headers, body, resp, resp_body):
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
        if not resp_body and resp.status >= 400:
            self.LOG.warning("status >= 400 response with empty body")

    def _request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        # Authenticate the request with the auth provider
        req_url, req_headers, req_body = self.auth_provider.auth_request(
            method, url, headers, body, self.filters)

        # Do the actual request, and time it
        start = time.time()
        resp, resp_body = self.http_obj.request(
            req_url, method, headers=req_headers, body=req_body)
        end = time.time()
        self._log_request(method, req_url, resp, secs=(end - start),
                          req_headers=req_headers, req_body=req_body,
                          resp_body=resp_body)

        # Verify HTTP response codes
        self.response_checker(method, url, req_headers, req_body, resp,
                              resp_body)

        return resp, resp_body

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        # if extra_headers is True
        # default headers would be added to headers
        retry = 0

        if headers is None:
            # NOTE(vponomaryov): if some client do not need headers,
            # it should explicitly pass empty dict
            headers = self.get_headers()
        elif extra_headers:
            try:
                headers = headers.copy()
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
        XML_ENC = ['application/xml', 'application/xml; charset=utf-8']

        if ctype.lower() in JSON_ENC or ctype.lower() in XML_ENC:
            parse_resp = True
        elif ctype.lower() in TXT_ENC:
            parse_resp = False
        else:
            raise exceptions.InvalidContentType(str(resp.status))

        if resp.status == 401 or resp.status == 403:
            raise exceptions.Unauthorized(resp_body)

        if resp.status == 404:
            raise exceptions.NotFound(resp_body)

        if resp.status == 400:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.BadRequest(resp_body)

        if resp.status == 409:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.Conflict(resp_body)

        if resp.status == 413:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            if self.is_absolute_limit(resp, resp_body):
                raise exceptions.OverLimit(resp_body)
            else:
                raise exceptions.RateLimitExceeded(resp_body)

        if resp.status == 422:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.UnprocessableEntity(resp_body)

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
                        elif 'error' in resp_body:  # Keystone errors
                            message = resp_body['error']['message']
                            raise exceptions.IdentityError(message)
                        elif 'message' in resp_body:
                            message = resp_body['message']
                    else:
                        message = resp_body

            raise exceptions.ServerFault(message)

        if resp.status >= 400:
            raise exceptions.UnexpectedResponseCode(str(resp.status))

    def is_absolute_limit(self, resp, resp_body):
        if (not isinstance(resp_body, collections.Mapping) or
                'retry-after' not in resp):
            return True
        if self._get_type() is "json":
            over_limit = resp_body.get('overLimit', None)
            if not over_limit:
                return True
            return 'exceed' in over_limit.get('message', 'blabla')
        elif self._get_type() is "xml":
            return 'exceed' in resp_body.get('message', 'blabla')

    def wait_for_resource_deletion(self, id):
        """Waits for a resource to be deleted."""
        start_time = int(time.time())
        while True:
            if self.is_resource_deleted(id):
                return
            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException
            time.sleep(self.build_interval)

    def is_resource_deleted(self, id):
        """
        Subclasses override with specific deletion detection.
        """
        message = ('"%s" does not implement is_resource_deleted'
                   % self.__class__.__name__)
        raise NotImplementedError(message)

    @classmethod
    def validate_response(cls, schema, resp, body):
        # Only check the response if the status code is a success code
        # TODO(cyeoh): Eventually we should be able to verify that a failure
        # code if it exists is something that we expect. This is explicitly
        # declared in the V3 API and so we should be able to export this in
        # the response schema. For now we'll ignore it.
        if resp.status in HTTP_SUCCESS:
            response_code = schema['status_code']
            if resp.status not in response_code:
                msg = ("The status code(%s) is different than the expected "
                       "one(%s)") % (resp.status, response_code)
                raise exceptions.InvalidHttpSuccessCode(msg)

            # Check the body of a response
            body_schema = schema.get('response_body')
            if body_schema:
                try:
                    jsonschema.validate(body, body_schema)
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
                    jsonschema.validate(resp, header_schema)
                except jsonschema.ValidationError as ex:
                    msg = ("HTTP response header is invalid (%s)") % ex
                    raise exceptions.InvalidHTTPResponseHeader(msg)


class NegativeRestClient(RestClient):
    """
    Version of RestClient that does not raise exceptions.
    """
    def _error_checker(self, method, url,
                       headers, body, resp, resp_body):
        pass

    def send_request(self, method, url_template, resources, body=None):
        url = url_template % tuple(resources)
        if method == "GET":
            resp, body = self.get(url)
        elif method == "POST":
            resp, body = self.post(url, body)
        elif method == "PUT":
            resp, body = self.put(url, body)
        elif method == "PATCH":
            resp, body = self.patch(url, body)
        elif method == "HEAD":
            resp, body = self.head(url)
        elif method == "DELETE":
            resp, body = self.delete(url)
        elif method == "COPY":
            resp, body = self.copy(url)
        else:
            assert False

        return resp, body
