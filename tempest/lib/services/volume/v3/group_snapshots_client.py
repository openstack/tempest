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
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.volume import base_client


class GroupSnapshotsClient(base_client.BaseClient):
    """Client class to send CRUD Volume Group Snapshot API requests"""

    def create_group_snapshot(self, **kwargs):
        """Creates a group snapshot.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#create-group-snapshot
        """
        post_body = json.dumps({'group_snapshot': kwargs})
        resp, body = self.post('group_snapshots', post_body)
        body = json.loads(body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_group_snapshot(self, group_snapshot_id):
        """Deletes a group snapshot.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#delete-group-snapshot
        """
        resp, body = self.delete('group_snapshots/%s' % group_snapshot_id)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_group_snapshot(self, group_snapshot_id):
        """Returns the details of a single group snapshot.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#show-group-snapshot-details
        """
        url = "group_snapshots/%s" % str(group_snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_group_snapshots(self, detail=False, **params):
        """Information for all the tenant's group snapshots.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#list-group-snapshots
        https://docs.openstack.org/api-ref/block-storage/v3/#list-group-snapshots-with-details
        """
        url = "group_snapshots"
        if detail:
            url += "/detail"
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_group_snapshot_status(self, group_snapshot_id, status_to_set):
        """Resets group snapshot status.

        For more information, please refer to the official API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/#reset-group-snapshot-status
        """
        post_body = json.dumps({'reset_status': {'status': status_to_set}})
        resp, body = self.post('group_snapshots/%s/action' % group_snapshot_id,
                               post_body)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_group_snapshot(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'group-snapshot'
