# Copyright 2013 OpenStack Foundation
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

"""
https://docs.openstack.org/api-ref/identity/v3/index.html#service-catalog-and-endpoints
"""

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class EndPointsClient(rest_client.RestClient):
    api_version = "v3"

    def list_endpoints(self, **params):
        """List endpoints.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-endpoints
        """
        url = 'endpoints'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_endpoint(self, **kwargs):
        """Create endpoint.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-endpoint
        """
        post_body = json.dumps({'endpoint': kwargs})
        resp, body = self.post('endpoints', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_endpoint(self, endpoint_id, **kwargs):
        """Updates an endpoint with given parameters.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-endpoint
        """
        post_body = json.dumps({'endpoint': kwargs})
        resp, body = self.patch('endpoints/%s' % endpoint_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_endpoint(self, endpoint_id):
        """Delete endpoint."""
        resp_header, resp_body = self.delete('endpoints/%s' % endpoint_id)
        self.expected_success(204, resp_header.status)
        return rest_client.ResponseBody(resp_header, resp_body)

    def show_endpoint(self, endpoint_id):
        """Get endpoint."""
        resp_header, resp_body = self.get('endpoints/%s' % endpoint_id)
        self.expected_success(200, resp_header.status)
        resp_body = json.loads(resp_body)
        return rest_client.ResponseBody(resp_header, resp_body)
