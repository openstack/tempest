# Copyright 2012 OpenStack Foundation
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
from tempest.services.volume.base import base_volumes_client


class VolumesClient(base_volumes_client.BaseVolumesClient):
    """Client class to send CRUD Volume V2 API requests"""
    api_version = "v2"
    create_resp = 202

    def update_volume_image_metadata(self, volume_id, **kwargs):
        """Update image metadata for the volume.

        Available params: see http://developer.openstack.org/
                              api-ref-blockstorage-v2.html
                              #setVolumeimagemetadata
        """
        post_body = json.dumps({'os-set_image_metadata': {'metadata': kwargs}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_image_metadata(self, volume_id, key_name):
        """Delete image metadata item for the volume."""
        post_body = json.dumps({'os-unset_image_metadata': {'key': key_name}})
        url = "volumes/%s/action" % (volume_id)
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_pools(self, detail=False):
        # List all the volumes pools (hosts)
        url = 'scheduler-stats/get_pools'
        if detail:
            url += '?detail=True'

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
