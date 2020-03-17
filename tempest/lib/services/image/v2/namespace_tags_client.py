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


class NamespaceTagsClient(rest_client.RestClient):
    api_version = "v2"

    def create_namespace_tag(self, namespace, tag_name):
        """Adds a tag to the list of namespace tag definitions.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-tag-definition
        """
        url = 'metadefs/namespaces/%s/tags/%s' % (namespace,
                                                  tag_name)
        resp, body = self.post(url, None)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_namespace_tag(self, namespace, tag_name):
        """Gets a definition for a tag.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#get-tag-definition
        """
        url = 'metadefs/namespaces/%s/tags/%s' % (namespace,
                                                  tag_name)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_namespace_tag(self, namespace, tag_name, **kwargs):
        """Renames a tag definition.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#update-tag-definition
        """
        url = 'metadefs/namespaces/%s/tags/%s' % (namespace,
                                                  tag_name)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace_tag(self, namespace, tag_name):
        """Deletes a tag definition within a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#delete-tag-definition
        """
        url = 'metadefs/namespaces/%s/tags/%s' % (namespace, tag_name)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def create_namespace_tags(self, namespace, **kwargs):
        """Creates one or more tag definitions in a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#create-tags
        """
        url = 'metadefs/namespaces/%s/tags' % namespace
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_namespace_tags(self, namespace, **params):
        """Lists the tag definitions within a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#list-tags
        """
        url = 'metadefs/namespaces/%s/tags' % namespace
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace_tags(self, namespace):
        """Deletes all tag definitions within a namespace.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/metadefs-index.html#delete-all-tag-definitions
        """
        url = 'metadefs/namespaces/%s/tags' % namespace
        resp, _ = self.delete(url)

        self.expected_success(204, resp.status)

        return rest_client.ResponseBody(resp)
