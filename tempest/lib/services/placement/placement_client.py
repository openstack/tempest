# Copyright (c) 2019 Ericsson
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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib.services.placement import base_placement_client


class PlacementClient(base_placement_client.BasePlacementClient):

    def list_allocation_candidates(self, **params):
        """List allocation candidates.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-allocation-candidates
        """
        url = '/allocation_candidates'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_allocations(self, consumer_uuid):
        """List all allocation records for the consumer.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-allocations
        """
        url = '/allocations/%s' % consumer_uuid
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
