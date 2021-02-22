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


class ProtocolsClient(rest_client.RestClient):

    def add_protocol_to_identity_provider(self, idp_id, protocol_id,
                                          **kwargs):
        """Add protocol to identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#add-protocol-to-identity-provider
        """
        post_body = json.dumps({'protocol': kwargs})
        resp, body = self.put(
            'OS-FEDERATION/identity_providers/%s/protocols/%s'
            % (idp_id, protocol_id), post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_protocols_of_identity_provider(self, idp_id, **kwargs):
        """List protocols of identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#list-protocols-of-identity-provider
        """
        url = 'OS-FEDERATION/identity_providers/%s/protocols' % idp_id
        if kwargs:
            url += '?%s' % urllib.urlencode(kwargs)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def get_protocol_for_identity_provider(self, idp_id, protocol_id):
        """Get protocol for identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#get-protocol-for-identity-provider
        """
        resp, body = self.get(
            'OS-FEDERATION/identity_providers/%s/protocols/%s'
            % (idp_id, protocol_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_mapping_for_identity_provider(self, idp_id, protocol_id,
                                             **kwargs):
        """Update attribute mapping for identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#update-attribute-mapping-for-identity-provider
        """
        post_body = json.dumps({'protocol': kwargs})
        resp, body = self.patch(
            'OS-FEDERATION/identity_providers/%s/protocols/%s'
            % (idp_id, protocol_id), post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_protocol_from_identity_provider(self, idp_id, protocol_id):
        """Delete a protocol from identity provider.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-a-protocol-from-identity-provider
        """
        resp, body = self.delete(
            'OS-FEDERATION/identity_providers/%s/protocols/%s'
            % (idp_id, protocol_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
