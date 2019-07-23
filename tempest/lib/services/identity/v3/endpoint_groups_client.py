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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class EndPointGroupsClient(rest_client.RestClient):
    api_version = "v3"

    def create_endpoint_group(self, **kwargs):
        """Create endpoint group.

        For a full list of available parameters, please refer to the
        official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#create-endpoint-group
        """
        post_body = json.dumps({'endpoint_group': kwargs})
        resp, body = self.post('OS-EP-FILTER/endpoint_groups', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_endpoint_group(self, endpoint_group_id, **kwargs):
        """Update endpoint group.

        For a full list of available parameters, please refer to the
        official API reference:
        https://docs.openstack.org/api-ref/identity/v3-ext/#update-endpoint-group
        """
        post_body = json.dumps({'endpoint_group': kwargs})
        resp, body = self.patch(
            'OS-EP-FILTER/endpoint_groups/%s' % endpoint_group_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_endpoint_group(self, endpoint_group_id):
        """Delete endpoint group."""
        resp_header, resp_body = self.delete(
            'OS-EP-FILTER/endpoint_groups/%s' % endpoint_group_id)
        self.expected_success(204, resp_header.status)
        return rest_client.ResponseBody(resp_header, resp_body)

    def show_endpoint_group(self, endpoint_group_id):
        """Get endpoint group."""
        resp_header, resp_body = self.get(
            'OS-EP-FILTER/endpoint_groups/%s' % endpoint_group_id)
        self.expected_success(200, resp_header.status)
        resp_body = json.loads(resp_body)
        return rest_client.ResponseBody(resp_header, resp_body)

    def check_endpoint_group(self, endpoint_group_id):
        """Check endpoint group."""
        resp_header, resp_body = self.head(
            'OS-EP-FILTER/endpoint_groups/%s' % endpoint_group_id)
        self.expected_success(200, resp_header.status)
        return rest_client.ResponseBody(resp_header, resp_body)

    def list_endpoint_groups(self):
        """Get endpoint groups."""
        resp_header, resp_body = self.get('OS-EP-FILTER/endpoint_groups')
        self.expected_success(200, resp_header.status)
        resp_body = json.loads(resp_body)
        return rest_client.ResponseBody(resp_header, resp_body)
