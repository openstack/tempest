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
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class NamespaceObjectsClient(rest_client.RestClient):
    api_version = "v2"

    def list_namespace_objects(self, namespace, **kwargs):
        """Lists all namespace objects.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-objects
        """
        url = 'metadefs/namespaces/%s/objects' % namespace
        if kwargs:
            url += '?%s' % urllib.urlencode(kwargs)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_namespace_object(self, namespace, **kwargs):
        """Create a namespace object

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-object
        """
        url = 'metadefs/namespaces/%s/objects' % namespace
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_namespace_object(self, namespace, object_name, **kwargs):
        """Update a namespace object

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#update-object
        """
        url = 'metadefs/namespaces/%s/objects/%s' % (namespace, object_name)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_namespace_object(self, namespace, object_name):
        """Show a namespace object

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#show-object
        """
        url = 'metadefs/namespaces/%s/objects/%s' % (namespace, object_name)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace_object(self, namespace, object_name):
        """Delete a namespace object

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#delete-object
        """
        url = 'metadefs/namespaces/%s/objects/%s' % (namespace, object_name)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
