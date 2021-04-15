# Copyright 2017 AT&T Corp
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

from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class AssistedVolumeSnapshotsClient(base_compute_client.BaseComputeClient):
    """Service client for assisted volume snapshots"""

    def delete_assisted_volume_snapshot(self, volume_id, snapshot_id):
        """Delete snapshot for the given volume id.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-assisted-volume-snapshot

        :param volume_id: UUID of the volume
        :param snapshot_id: The UUID of the snapshot
        """
        query_param = {'delete_info': json.dumps({'volume_id': volume_id})}
        resp, body = self.delete("os-assisted-volume-snapshots/%s?%s"
                                 % (snapshot_id,
                                    urllib.urlencode(query_param)))
        return rest_client.ResponseBody(resp, body)

    def create_assisted_volume_snapshot(self, volume_id, snapshot_id,
                                        **kwargs):
        """Create a new assisted volume snapshot.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-assisted-volume-snapshots

        :param volume_id: the source volume ID
        :param snapshot_id: the UUID for a snapshot
        :param type: Type of snapshot, such as qcow2
        :param new_file: The name of image file that will be created
        """
        url = "os-assisted-volume-snapshots"
        info = {"snapshot_id": snapshot_id}
        if kwargs:
            info.update(kwargs)
        body = {"snapshot": {"volume_id": volume_id, "create_info": info}}
        post_body = json.dumps(body)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
