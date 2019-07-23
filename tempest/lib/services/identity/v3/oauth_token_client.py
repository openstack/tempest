# Copyright 2017 AT&T Corporation.
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

import binascii
import hashlib
import hmac
import random
import time

import six
from six.moves.urllib import parse as urlparse

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class OAUTHTokenClient(rest_client.RestClient):
    api_version = "v3"

    def _escape(self, s):
        """Escape a unicode string in an OAuth-compatible fashion."""
        safe = b'~'
        s = s.encode('utf-8') if isinstance(s, six.text_type) else s
        s = urlparse.quote(s, safe)
        if isinstance(s, six.binary_type):
            s = s.decode('utf-8')
        return s

    def _generate_params_with_signature(self, client_key, uri,
                                        client_secret=None,
                                        resource_owner_key=None,
                                        resource_owner_secret=None,
                                        callback_uri=None,
                                        verifier=None,
                                        http_method='GET'):
        """Generate OAUTH params along with signature."""
        timestamp = six.text_type(int(time.time()))
        nonce = six.text_type(random.getrandbits(64)) + timestamp
        oauth_params = [
            ('oauth_nonce', nonce),
            ('oauth_timestamp', timestamp),
            ('oauth_version', '1.0'),
            ('oauth_signature_method', 'HMAC-SHA1'),
            ('oauth_consumer_key', client_key),
        ]
        if resource_owner_key:
            oauth_params.append(('oauth_token', resource_owner_key))
        if callback_uri:
            oauth_params.append(('oauth_callback', callback_uri))
        if verifier:
            oauth_params.append(('oauth_verifier', verifier))

        # normalize_params
        key_values = [(self._escape(k), self._escape(v))
                      for k, v in oauth_params]
        key_values.sort()
        parameter_parts = ['{0}={1}'.format(k, v) for k, v in key_values]
        normalized_params = '&'.join(parameter_parts)

        # normalize_uri
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(uri)
        scheme = scheme.lower()
        netloc = netloc.lower()
        path = path.replace('//', '/')
        normalized_uri = urlparse.urlunparse((scheme, netloc, path,
                                              params, '', ''))

        # construct base string
        base_string = self._escape(http_method.upper())
        base_string += '&'
        base_string += self._escape(normalized_uri)
        base_string += '&'
        base_string += self._escape(normalized_params)

        # sign using hmac-sha1
        key = self._escape(client_secret or '')
        key += '&'
        key += self._escape(resource_owner_secret or '')
        key_utf8 = key.encode('utf-8')
        text_utf8 = base_string.encode('utf-8')
        signature = hmac.new(key_utf8, text_utf8, hashlib.sha1)
        sig = binascii.b2a_base64(signature.digest())[:-1].decode('utf-8')

        oauth_params.append(('oauth_signature', sig))
        return oauth_params

    def _generate_oauth_header(self, oauth_params):
        authorization_header = {}
        authorization_header_parameters_parts = []
        for oauth_parameter_name, value in oauth_params:
            escaped_name = self._escape(oauth_parameter_name)
            escaped_value = self._escape(value)
            part = '{0}="{1}"'.format(escaped_name, escaped_value)
            authorization_header_parameters_parts.append(part)

        authorization_header_parameters = ', '.join(
            authorization_header_parameters_parts)
        oauth_string = 'OAuth %s' % authorization_header_parameters
        authorization_header['Authorization'] = oauth_string

        return authorization_header

    def create_request_token(self, consumer_key, consumer_secret, project_id):
        """Create request token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#create-request-token
        """
        endpoint = 'OS-OAUTH1/request_token'
        headers = {'Requested-Project-Id': project_id}
        oauth_params = self._generate_params_with_signature(
            consumer_key,
            self.base_url + '/' + endpoint,
            client_secret=consumer_secret,
            callback_uri='oob',
            http_method='POST')
        oauth_header = self._generate_oauth_header(oauth_params)
        headers.update(oauth_header)
        resp, body = self.post(endpoint,
                               body=None,
                               headers=headers)
        self.expected_success(201, resp.status)
        if not isinstance(body, str):
            body = body.decode('utf-8')
        body = dict(item.split("=") for item in body.split("&"))
        return rest_client.ResponseBody(resp, body)

    def authorize_request_token(self, request_token_id, role_ids):
        """Authorize request token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#authorize-request-token
        """
        roles = [{'id': role_id} for role_id in role_ids]
        body = {'roles': roles}
        post_body = json.dumps(body)
        resp, body = self.put("OS-OAUTH1/authorize/%s" % request_token_id,
                              post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_access_token(self, consumer_key, consumer_secret, request_key,
                            request_secret, oauth_verifier):
        """Create access token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#create-access-token
        """
        endpoint = 'OS-OAUTH1/access_token'
        oauth_params = self._generate_params_with_signature(
            consumer_key,
            self.base_url + '/' + endpoint,
            client_secret=consumer_secret,
            resource_owner_key=request_key,
            resource_owner_secret=request_secret,
            verifier=oauth_verifier,
            http_method='POST')
        headers = self._generate_oauth_header(oauth_params)
        resp, body = self.post(endpoint, body=None, headers=headers)
        self.expected_success(201, resp.status)
        if not isinstance(body, str):
            body = body.decode('utf-8')
        body = dict(item.split("=") for item in body.split("&"))
        return rest_client.ResponseBody(resp, body)

    def get_access_token(self, user_id, access_token_id):
        """Get access token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#get-access-token
        """
        resp, body = self.get("users/%s/OS-OAUTH1/access_tokens/%s"
                              % (user_id, access_token_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def revoke_access_token(self, user_id, access_token_id):
        """Revoke access token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#revoke-access-token
        """
        resp, body = self.delete("users/%s/OS-OAUTH1/access_tokens/%s"
                                 % (user_id, access_token_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_access_tokens(self, user_id):
        """List access tokens.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#list-access-tokens
        """
        resp, body = self.get("users/%s/OS-OAUTH1/access_tokens"
                              % (user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_access_token_roles(self, user_id, access_token_id):
        """List roles for an access token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#list-roles-for-an-access-token
        """
        resp, body = self.get("users/%s/OS-OAUTH1/access_tokens/%s/roles"
                              % (user_id, access_token_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def get_access_token_role(self, user_id, access_token_id, role_id):
        """Show role details for an access token.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#show-role-details-for-an-access-token
        """
        resp, body = self.get("users/%s/OS-OAUTH1/access_tokens/%s/roles/%s"
                              % (user_id, access_token_id, role_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
