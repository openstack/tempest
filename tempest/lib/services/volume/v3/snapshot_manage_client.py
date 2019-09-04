# Copyright 2016 Red Hat, Inc.
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

from tempest.lib.api_schema.response.volume import manage_snapshot as schema
from tempest.lib.common import rest_client


class SnapshotManageClient(rest_client.RestClient):
    """Snapshot manage client."""

    def manage_snapshot(self, **kwargs):
        """Manage a snapshot.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#manage-an-existing-snapshot
        """
        post_body = json.dumps({'snapshot': kwargs})
        url = 'os-snapshot-manage'
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.manage_snapshot, resp, body)
        return rest_client.ResponseBody(resp, body)
