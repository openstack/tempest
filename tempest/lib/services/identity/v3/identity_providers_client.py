# Copyright 2020 Samsung Electronics Co., Ltd
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class IdentityProvidersClient(rest_client.RestClient):

    def register_identity_provider(self, identity_provider_id, **kwargs):
        """Register an identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#register-an-identity-provider
        """
        post_body = json.dumps({'identity_provider': kwargs})
        resp, body = self.put(
            'OS-FEDERATION/identity_providers/%s' % identity_provider_id,
            post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_identity_providers(self, **params):
        """List identity providers.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#list-identity-providers
        """
        url = 'identity_providers'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def get_identity_provider(self, identity_provider_id):
        """Get identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#get-identity-provider
        """
        resp, body = self.get(
            'OS-FEDERATION/identity_providers/%s' % identity_provider_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_identity_provider(self, identity_provider_id):
        """Delete identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-identity-provider
        """
        resp, body = self.delete(
            'OS-FEDERATION/identity_providers/%s' % identity_provider_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_identity_provider(self, identity_provider_id, **kwargs):
        """Update identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#update-identity-provider
        """
        post_body = json.dumps({'identity_provider': kwargs})
        resp, body = self.patch(
            'OS-FEDERATION/identity_providers/%s' % identity_provider_id,
            post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
