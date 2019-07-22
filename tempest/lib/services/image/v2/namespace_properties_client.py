# Copyright 2016 EasyStack.
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


class NamespacePropertiesClient(rest_client.RestClient):
    api_version = "v2"

    def list_namespace_properties(self, namespace):
        """Lists property definitions in a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-properties
        """
        url = 'metadefs/namespaces/%s/properties' % namespace
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_namespace_property(self, namespace, **kwargs):
        """Creates a property definition in a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-property
        """
        url = 'metadefs/namespaces/%s/properties' % namespace
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_namespace_properties(self, namespace, property_name):
        """Shows the definition for a property.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#show-property-definition
        """
        url = 'metadefs/namespaces/%s/properties/%s' % (namespace,
                                                        property_name)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_namespace_properties(self, namespace, property_name, **kwargs):
        """Updates a property definition.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#update-property-definition
        """
        url = 'metadefs/namespaces/%s/properties/%s' % (namespace,
                                                        property_name)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace_property(self, namespace, property_name):
        """Removes a property definition from a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#remove-property-definition
        """
        url = 'metadefs/namespaces/%s/properties/%s' % (namespace,
                                                        property_name)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
