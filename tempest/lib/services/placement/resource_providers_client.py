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


class ResourceProvidersClient(base_placement_client.BasePlacementClient):
    """Client class for resource provider related methods

    This client class aims to support read-only API operations for resource
    providers. The following resources are supported:
    * resource providers
    * resource provider inventories
    * resource provider aggregates
    * resource provider usages
    """

    def list_resource_providers(self, **params):
        """List resource providers.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-resource-providers
        """
        url = '/resource_providers'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_resource_provider(self, rp_uuid):
        """Show resource provider.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#show-resource-provider
        """
        url = '/resource_providers/%s' % rp_uuid
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_resource_provider_inventories(self, rp_uuid):
        """List resource provider inventories.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-resource-provider-inventories
        """
        url = '/resource_providers/%s/inventories' % rp_uuid
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_resource_provider_usages(self, rp_uuid):
        """List resource provider usages.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-resource-provider-usages
        """
        url = '/resource_providers/%s/usages' % rp_uuid
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_resource_provider_aggregates(self, rp_uuid):
        """List resource provider aggregates.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#list-resource-provider-aggregates
        """
        url = '/resource_providers/%s/aggregates' % rp_uuid
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_resource_providers_inventories(self, rp_uuid, **kwargs):
        """Update resource providers inventories.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#update-resource-provider-inventories
        """
        url = '/resource_providers/{}/inventories'.format(rp_uuid)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_resource_providers_inventories(self, rp_uuid):
        """Delete resource providers inventories.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/placement/#delete-resource-provider-inventories
        """
        url = '/resource_providers/{}/inventories'.format(rp_uuid)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
