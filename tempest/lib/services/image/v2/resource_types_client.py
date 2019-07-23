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


class ResourceTypesClient(rest_client.RestClient):
    api_version = "v2"

    def list_resource_types(self):
        """Lists all resource types.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-resource-types
        """
        url = 'metadefs/resource_types'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_resource_type_association(self, namespace_id, **kwargs):
        """Creates a resource type association in given namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-resource-type-association
        """
        url = 'metadefs/namespaces/%s/resource_types' % namespace_id
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_resource_type_association(self, namespace_id):
        """Lists resource type associations in given namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-resource-type-associations
        """
        url = 'metadefs/namespaces/%s/resource_types' % namespace_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_resource_type_association(self, namespace_id, resource_name):
        """Removes resource type association in given namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#remove-resource-type-association
        """
        url = 'metadefs/namespaces/%s/resource_types/%s' % (namespace_id,
                                                            resource_name)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
