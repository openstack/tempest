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
import hashlib
import json
from lxml import etree
import re
import time

from tempest.common import http
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.services.compute.xml.common import xml_to_json

CONF = config.CONF

# redrive rate limited calls at most twice
MAX_RECURSION_DEPTH = 2
TOKEN_CHARS_RE = re.compile('^[-A-Za-z0-9+/=]*$')

# All the successful HTTP status codes from RFC 2616
HTTP_SUCCESS = (200, 201, 202, 203, 204, 205, 206)


class RestClient(object):
    TYPE = "json"
    LOG = logging.getLogger(__name__)

    def __init__(self, user, password, auth_url, tenant_name=None,
                 auth_version='v2'):
        self.user = user
        self.password = password
        self.auth_url = auth_url
        self.tenant_name = tenant_name
        self.auth_version = auth_version

        self.service = None
        self.token = None
        self.base_url = None
        self.region = {}
        for cfgname in dir(CONF):
            # Find all config.FOO.catalog_type and assume FOO is a service.
            cfg = getattr(CONF, cfgname)
            catalog_type = getattr(cfg, 'catalog_type', None)
            if not catalog_type:
                continue
            service_region = getattr(cfg, 'region', None)
            if not service_region:
                service_region = CONF.identity.region
            self.region[catalog_type] = service_region
        self.endpoint_url = 'publicURL'
        self.headers = {'Content-Type': 'application/%s' % self.TYPE,
                        'Accept': 'application/%s' % self.TYPE}
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

    def __str__(self):
        STRING_LIMIT = 80
        str_format = ("user:%s, password:%s, "
                      "auth_url:%s, tenant_name:%s, auth_version:%s, "
                      "service:%s, base_url:%s, region:%s, "
                      "endpoint_url:%s, build_interval:%s, build_timeout:%s"
                      "\ntoken:%s..., \nheaders:%s...")
        return str_format % (self.user, self.password,
                             self.auth_url, self.tenant_name,
                             self.auth_version, self.service,
                             self.base_url, self.region, self.endpoint_url,
                             self.build_interval, self.build_timeout,
                             str(self.token)[0:STRING_LIMIT],
                             str(self.headers)[0:STRING_LIMIT])

    def _set_auth(self):
        """
        Sets the token and base_url used in requests based on the strategy type
        """

        if self.auth_version == 'v3':
            auth_func = self.identity_auth_v3
        else:
            auth_func = self.keystone_auth

        self.token, self.base_url = (
            auth_func(self.user, self.password, self.auth_url,
                      self.service, self.tenant_name))

    def clear_auth(self):
        """
        Can be called to clear the token and base_url so that the next request
        will fetch a new token and base_url.
        """

        self.token = None
        self.base_url = None

    def get_auth(self):
        """Returns the token of the current request or sets the token if
        none.
        """

        if not self.token:
            self._set_auth()

        return self.token

    def keystone_auth(self, user, password, auth_url, service, tenant_name):
        """
        Provides authentication via Keystone using v2 identity API.
        """

        # Normalize URI to ensure /tokens is in it.
        if 'tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/tokens'

        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                },
                'tenantName': tenant_name,
            }
        }

        headers = {'Content-Type': 'application/json'}
        body = json.dumps(creds)
        self._log_request('POST', auth_url, headers, body)
        resp, resp_body = self.http_obj.request(auth_url, 'POST',
                                                headers=headers, body=body)
        self._log_response(resp, resp_body)

        if resp.status == 200:
            try:
                auth_data = json.loads(resp_body)['access']
                token = auth_data['token']['id']
            except Exception as e:
                print("Failed to obtain token for user: %s" % e)
                raise

            mgmt_url = None
            for ep in auth_data['serviceCatalog']:
                if ep["type"] == service:
                    for _ep in ep['endpoints']:
                        if service in self.region and \
                                _ep['region'] == self.region[service]:
                            mgmt_url = _ep[self.endpoint_url]
                    if not mgmt_url:
                        mgmt_url = ep['endpoints'][0][self.endpoint_url]
                    break

            if mgmt_url is None:
                raise exceptions.EndpointNotFound(service)

            return token, mgmt_url

        elif resp.status == 401:
            raise exceptions.AuthenticationFailure(user=user,
                                                   password=password,
                                                   tenant=tenant_name)
        raise exceptions.IdentityError('Unexpected status code {0}'.format(
            resp.status))

    def identity_auth_v3(self, user, password, auth_url, service,
                         project_name, domain_id='default'):
        """Provides authentication using Identity API v3."""

        req_url = auth_url.rstrip('/') + '/auth/tokens'

        creds = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": user, "password": password,
                            "domain": {"id": domain_id}
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {"id": domain_id},
                        "name": project_name
                    }
                }
            }
        }

        headers = {'Content-Type': 'application/json'}
        body = json.dumps(creds)
        resp, body = self.http_obj.request(req_url, 'POST',
                                           headers=headers, body=body)

        if resp.status == 201:
            try:
                token = resp['x-subject-token']
            except Exception:
                self.LOG.exception("Failed to obtain token using V3"
                                   " authentication (auth URL is '%s')" %
                                   req_url)
                raise

            catalog = json.loads(body)['token']['catalog']

            mgmt_url = None
            for service_info in catalog:
                if service_info['type'] != service:
                    continue  # this isn't the entry for us.

                endpoints = service_info['endpoints']

                # Look for an endpoint in the region if configured.
                if service in self.region:
                    region = self.region[service]

                    for ep in endpoints:
                        if ep['region'] != region:
                            continue

                        mgmt_url = ep['url']
                        # FIXME(blk-u): this isn't handling endpoint type
                        # (public, internal, admin).
                        break

                if not mgmt_url:
                    # Didn't find endpoint for region, use the first.

                    ep = endpoints[0]
                    mgmt_url = ep['url']
                    # FIXME(blk-u): this isn't handling endpoint type
                    # (public, internal, admin).

                break

            return token, mgmt_url

        elif resp.status == 401:
            raise exceptions.AuthenticationFailure(user=user,
                                                   password=password,
                                                   tenant=project_name)
        else:
            self.LOG.error("Failed to obtain token using V3 authentication"
                           " (auth URL is '%s'), the response status is %s" %
                           (req_url, resp.status))
            raise exceptions.AuthenticationFailure(user=user,
                                                   password=password,
                                                   tenant=project_name)

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

    def post(self, url, body, headers):
        return self.request('POST', url, headers, body)

    def get(self, url, headers=None):
        return self.request('GET', url, headers)

    def delete(self, url, headers=None, body=None):
        return self.request('DELETE', url, headers, body)

    def patch(self, url, body, headers):
        return self.request('PATCH', url, headers, body)

    def put(self, url, body, headers):
        return self.request('PUT', url, headers, body)

    def head(self, url, headers=None):
        return self.request('HEAD', url, headers)

    def copy(self, url, headers=None):
        return self.request('COPY', url, headers)

    def get_versions(self):
        resp, body = self.get('')
        body = self._parse_resp(body)
        body = body['versions']
        versions = map(lambda x: x['id'], body)
        return resp, versions

    def _log_request(self, method, req_url, headers, body):
        self.LOG.info('Request: ' + method + ' ' + req_url)
        if headers:
            print_headers = headers
            if 'X-Auth-Token' in headers and headers['X-Auth-Token']:
                token = headers['X-Auth-Token']
                if len(token) > 64 and TOKEN_CHARS_RE.match(token):
                    print_headers = headers.copy()
                    print_headers['X-Auth-Token'] = "<Token omitted>"
            self.LOG.debug('Request Headers: ' + str(print_headers))
        if body:
            str_body = str(body)
            length = len(str_body)
            self.LOG.debug('Request Body: ' + str_body[:2048])
            if length >= 2048:
                self.LOG.debug("Large body (%d) md5 summary: %s", length,
                               hashlib.md5(str_body).hexdigest())

    def _log_response(self, resp, resp_body):
        status = resp['status']
        self.LOG.info("Response Status: " + status)
        headers = resp.copy()
        del headers['status']
        if headers.get('x-compute-request-id'):
            self.LOG.info("Nova request id: %s" %
                          headers.pop('x-compute-request-id'))
        elif headers.get('x-openstack-request-id'):
            self.LOG.info("Glance request id %s" %
                          headers.pop('x-openstack-request-id'))
        if len(headers):
            self.LOG.debug('Response Headers: ' + str(headers))
        if resp_body:
            str_body = str(resp_body)
            length = len(str_body)
            self.LOG.debug('Response Body: ' + str_body[:2048])
            if length >= 2048:
                self.LOG.debug("Large body (%d) md5 summary: %s", length,
                               hashlib.md5(str_body).hexdigest())

    def _parse_resp(self, body):
        return json.loads(body)

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

    def _request(self, method, url,
                 headers=None, body=None):
        """A simple HTTP request interface."""

        req_url = "%s/%s" % (self.base_url, url)
        self._log_request(method, req_url, headers, body)
        resp, resp_body = self.http_obj.request(req_url, method,
                                                headers=headers, body=body)
        self._log_response(resp, resp_body)
        self.response_checker(method, url, headers, body, resp, resp_body)

        return resp, resp_body

    def request(self, method, url,
                headers=None, body=None):
        retry = 0
        if (self.token is None) or (self.base_url is None):
            self._set_auth()

        if headers is None:
            headers = {}
        headers['X-Auth-Token'] = self.token

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
            raise exceptions.RestClientException(str(resp.status))

        if resp.status == 401 or resp.status == 403:
            raise exceptions.Unauthorized()

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

            raise exceptions.ServerFault(message)

        if resp.status >= 400:
            if parse_resp:
                resp_body = self._parse_resp(resp_body)
            raise exceptions.RestClientException(str(resp.status))

    def is_absolute_limit(self, resp, resp_body):
        if (not isinstance(resp_body, collections.Mapping) or
                'retry-after' not in resp):
            return True
        over_limit = resp_body.get('overLimit', None)
        if not over_limit:
            return True
        return 'exceed' in over_limit.get('message', 'blabla')

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


class RestClientXML(RestClient):
    TYPE = "xml"

    def _parse_resp(self, body):
        return xml_to_json(etree.fromstring(body))

    def is_absolute_limit(self, resp, resp_body):
        if (not isinstance(resp_body, collections.Mapping) or
                'retry-after' not in resp):
            return True
        return 'exceed' in resp_body.get('message', 'blabla')
