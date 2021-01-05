# Copyright 2014 Hewlett-Packard Development Company, L.P
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
https://docs.openstack.org/api-ref/identity/v3/index.html#regions
"""

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class RegionsClient(rest_client.RestClient):
    api_version = "v3"

    def create_region(self, region_id=None, **kwargs):
        """Create region.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-region
        """
        if region_id is not None:
            method = self.put
            url = 'regions/%s' % region_id
        else:
            method = self.post
            url = 'regions'
        req_body = json.dumps({'region': kwargs})
        resp, body = method(url, req_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_region(self, region_id, **kwargs):
        """Updates a region.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-region
        """
        post_body = json.dumps({'region': kwargs})
        resp, body = self.patch('regions/%s' % region_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_region(self, region_id):
        """Get region."""
        url = 'regions/%s' % region_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_regions(self, params=None):
        """List regions."""
        url = 'regions'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_region(self, region_id):
        """Delete region."""
        resp, body = self.delete('regions/%s' % region_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
