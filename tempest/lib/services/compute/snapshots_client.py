# Copyright 2015 Fujitsu(fnst) Corporation
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

from tempest.lib.api_schema.response.compute.v2_1 import snapshots as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import base_compute_client


class SnapshotsClient(base_compute_client.BaseComputeClient):

    def create_snapshot(self, volume_id, **kwargs):
        """Create a snapshot.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-snapshot
        """
        post_body = {
            'volume_id': volume_id
        }
        post_body.update(kwargs)
        post_body = json.dumps({'snapshot': post_body})
        resp, body = self.post('os-snapshots', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_get_snapshot, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_snapshot(self, snapshot_id):
        url = "os-snapshots/%s" % snapshot_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.create_get_snapshot, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_snapshots(self, detail=False, params=None):
        """List snapshots.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-snapshots
        """
        url = 'os-snapshots'

        if detail:
            url += '/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_snapshots, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_snapshot(self, snapshot_id):
        resp, body = self.delete("os-snapshots/%s" % snapshot_id)
        self.validate_response(schema.delete_snapshot, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_snapshot(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'snapshot'
