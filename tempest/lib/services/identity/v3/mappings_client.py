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


class MappingsClient(rest_client.RestClient):

    def create_mapping(self, mapping_id, **kwargs):
        """Create a mapping.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#create-a-mapping
        """
        post_body = json.dumps({'mapping': kwargs})
        resp, body = self.put(
            'OS-FEDERATION/mappings/%s' % mapping_id, post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def get_mapping(self, mapping_id):
        """Get a mapping.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#get-a-mapping
        """
        resp, body = self.get(
            'OS-FEDERATION/mappings/%s' % mapping_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_mapping(self, mapping_id, **kwargs):
        """Update a mapping.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#update-a-mapping
        """
        post_body = json.dumps({'mapping': kwargs})
        resp, body = self.patch(
            'OS-FEDERATION/mappings/%s' % mapping_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_mappings(self, **kwargs):
        """List mappings.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#list-mappings
        """
        url = 'OS-FEDERATION/mappings'
        if kwargs:
            url += '?%s' % urllib.urlencode(kwargs)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_mapping(self, mapping_id):
        """Delete a mapping.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/index.html#delete-a-mapping
        """
        resp, body = self.delete(
            'OS-FEDERATION/mappings/%s' % mapping_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
