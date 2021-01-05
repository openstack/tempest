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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.volume import groups as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume import base_client


class GroupsClient(base_client.BaseClient):
    """Client class to send CRUD Volume Group API requests"""
    api_version = 'v3'

    def create_group(self, **kwargs):
        """Creates a group.

        group_type and volume_types are required parameters in kwargs.
        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#create-group
        """
        post_body = json.dumps({'group': kwargs})
        resp, body = self.post('groups', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_group(self, group_id, delete_volumes=True):
        """Deletes a group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#delete-group
        """
        post_body = {'delete-volumes': delete_volumes}
        post_body = json.dumps({'delete': post_body})
        resp, body = self.post('groups/%s/action' % group_id,
                               post_body)
        self.validate_response(schema.delete_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_group(self, group_id):
        """Returns the details of a single group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#show-group-details
        """
        url = "groups/%s" % str(group_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_groups(self, detail=False, **params):
        """Lists information for all the tenant's groups.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#list-groups
        https://docs.openstack.org/api-ref/block-storage/v3/#list-groups-with-details
        """
        url = "groups"
        schema_list_groups = schema.list_groups_no_detail
        if detail:
            url += "/detail"
            schema_list_groups = schema.list_groups_with_detail
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema_list_groups, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_group_from_source(self, **kwargs):
        """Creates a group from source.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#create-group-from-source
        """
        post_body = json.dumps({'create-from-src': kwargs})
        resp, body = self.post('groups/action', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_group_from_source, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_group(self, group_id, **kwargs):
        """Updates the specified group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#update-group
        """
        put_body = json.dumps({'group': kwargs})
        resp, body = self.put('groups/%s' % group_id, put_body)
        self.validate_response(schema.update_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def reset_group_status(self, group_id, status_to_set):
        """Resets group status.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#reset-group-status
        """
        post_body = json.dumps({'reset_status': {'status': status_to_set}})
        resp, body = self.post('groups/%s/action' % group_id, post_body)
        self.validate_response(schema.reset_group_status, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_group(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'group'
