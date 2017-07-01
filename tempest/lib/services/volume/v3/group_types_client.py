# Copyright (C) 2017 Dell Inc. or its subsidiaries.
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
from tempest.lib.services.volume import base_client


class GroupTypesClient(base_client.BaseClient):
    """Client class to send CRUD Volume V3 Group Types API requests"""
    api_version = 'v3'

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'group-type'

    def create_group_type(self, **kwargs):
        """Create group_type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#create-group-type
        """
        post_body = json.dumps({'group_type': kwargs})
        resp, body = self.post('group_types', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_group_type(self, group_type_id):
        """Deletes the specified group_type."""
        resp, body = self.delete("group_types/%s" % group_type_id)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_group_types(self, **params):
        """List all the group_types created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#list-group-types
        """
        url = 'group_types'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_group_type(self, group_type_id):
        """Returns the details of a single group_type.

        For more information, please refer to the official API reference:
        https://developer.openstack.org/api-ref/block-storage/v3/#show-group-type-details
        """
        url = "group_types/%s" % group_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
