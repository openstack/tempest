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
from tempest.lib.services.network import base


class TagsClient(base.BaseNetworkClient):

    def create_tag(self, resource_type, resource_id, tag):
        """Adds a tag on the resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#add-a-tag
        """
        uri = '/%s/%s/tags/%s' % (resource_type, resource_id, tag)
        return self.update_resource(
            uri, json.dumps({}), expect_response_code=201,
            expect_empty_body=True)

    def check_tag_existence(self, resource_type, resource_id, tag):
        """Confirm that a given tag is set on the resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#confirm-a-tag
        """
        # TODO(felipemonteiro): Use the "check_resource" method in
        # ``BaseNetworkClient`` once it has been implemented.
        uri = '%s/%s/%s/tags/%s' % (
            self.uri_prefix, resource_type, resource_id, tag)
        resp, _ = self.get(uri)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def update_all_tags(self, resource_type, resource_id, tags):
        """Replace all tags on the resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#replace-all-tags
        """
        uri = '/%s/%s/tags' % (resource_type, resource_id)
        put_body = {"tags": tags}
        return self.update_resource(uri, put_body)

    def delete_tag(self, resource_type, resource_id, tag):
        """Removes a tag on the resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#remove-a-tag
        """
        uri = '/%s/%s/tags/%s' % (resource_type, resource_id, tag)
        return self.delete_resource(uri)

    def delete_all_tags(self, resource_type, resource_id):
        """Removes all tags on the resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#remove-all-tags
        """
        uri = '/%s/%s/tags' % (resource_type, resource_id)
        return self.delete_resource(uri)

    def list_tags(self, resource_type, resource_id):
        """Retrieves the tags for a resource.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#obtain-tag-list
        """
        uri = '/%s/%s/tags' % (resource_type, resource_id)
        return self.list_resources(uri)
