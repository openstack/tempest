# Copyright 2013 IBM Corp.
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


class NamespacesClient(rest_client.RestClient):
    api_version = "v2"

    def create_namespace(self, **kwargs):
        """Create a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-namespace
        """
        data = json.dumps(kwargs)
        resp, body = self.post('metadefs/namespaces', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_namespaces(self):
        """List namespaces

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-namespaces
        """
        url = 'metadefs/namespaces'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_namespace(self, namespace):
        """Show namespace details.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#get-namespace-details
        """
        url = 'metadefs/namespaces/%s' % namespace
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_namespace(self, namespace, **kwargs):
        """Update a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#update-namespace
        """
        # NOTE: On Glance API, we need to pass namespace on both URI
        # and a request body.
        params = {'namespace': namespace}
        params.update(kwargs)
        data = json.dumps(params)
        url = 'metadefs/namespaces/%s' % namespace
        resp, body = self.put(url, body=data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace(self, namespace):
        """Delete a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#delete-namespace
        """
        url = 'metadefs/namespaces/%s' % namespace
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
