# Copyright 2015 NEC Corporation.  All rights reserved.
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

from oslo_log import log as logging
from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions


class TokenClient(rest_client.RestClient):

    def __init__(self, auth_url, disable_ssl_certificate_validation=None,
                 ca_certs=None, trace_requests=None, **kwargs):
        """Initialises the Token client

        :param auth_url: URL to which the token request is sent
        :param disable_ssl_certificate_validation: pass-through to rest client
        :param ca_certs: pass-through to rest client
        :param trace_requests: pass-through to rest client
        :param kwargs: any extra parameter to pass through the rest client.
               region, service and auth_provider will be ignored, if passed,
               as they are not meaningful for token client
        """
        dscv = disable_ssl_certificate_validation
        # NOTE(andreaf) region, service and auth_provider are passed
        # positionally with None. Having them in kwargs would raise a
        # "multiple values for keyword arguments" error
        for unwanted_kwargs in ['region', 'service', 'auth_provider']:
            kwargs.pop(unwanted_kwargs, None)
        super(TokenClient, self).__init__(
            None, None, None, disable_ssl_certificate_validation=dscv,
            ca_certs=ca_certs, trace_requests=trace_requests, **kwargs)

        if auth_url is None:
            raise exceptions.IdentityError("Couldn't determine auth_url")

        # Normalize URI to ensure /tokens is in it.
        if 'tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/tokens'

        self.auth_url = auth_url

    def auth(self, user, password, tenant=None):
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                },
            }
        }

        if tenant:
            creds['auth']['tenantName'] = tenant

        body = json.dumps(creds, sort_keys=True)
        resp, body = self.post(self.auth_url, body=body)
        self.expected_success(200, resp.status)

        return rest_client.ResponseBody(resp, body['access'])

    def auth_token(self, token_id, tenant=None):
        creds = {
            'auth': {
                'token': {
                    'id': token_id,
                },
            }
        }

        if tenant:
            creds['auth']['tenantName'] = tenant

        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, body=body)
        self.expected_success(200, resp.status)

        return rest_client.ResponseBody(resp, body['access'])

    def request(self, method, url, extra_headers=False, headers=None,
                body=None, chunked=False):
        """A simple HTTP request interface.

        Note: this overloads the `request` method from the parent class and
        thus must implement the same method signature.
        """
        if headers is None:
            headers = self.get_headers(accept_type="json")
        elif extra_headers:
            try:
                headers.update(self.get_headers(accept_type="json"))
            except (ValueError, TypeError):
                headers = self.get_headers(accept_type="json")

        resp, resp_body = self.raw_request(url, method,
                                           headers=headers, body=body,
                                           log_req_body='<omitted>')

        if resp.status in [401, 403]:
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])
        elif resp.status not in [200, 201]:
            raise exceptions.IdentityError(
                'Unexpected status code {0}'.format(resp.status))

        return resp, json.loads(resp_body)

    def get_token(self, user, password, tenant, auth_data=False):
        """Returns (token id, token data) for supplied credentials."""
        body = self.auth(user, password, tenant)

        if auth_data:
            return body['token']['id'], body
        else:
            return body['token']['id']


class TokenClientJSON(TokenClient):
    LOG = logging.getLogger(__name__)

    def _warn(self):
        self.LOG.warning("%s class was deprecated and renamed to %s",
                         self.__class__.__name__, 'TokenClient')

    def __init__(self, *args, **kwargs):
        self._warn()
        super(TokenClientJSON, self).__init__(*args, **kwargs)
