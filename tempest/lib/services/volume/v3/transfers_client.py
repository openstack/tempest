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
from six.moves.urllib import parse as urllib

from tempest.lib.api_schema.response.volume import transfers as schema
from tempest.lib.common import rest_client


class TransfersClient(rest_client.RestClient):
    """Client class to send CRUD Volume Transfer API requests"""

    def create_volume_transfer(self, **kwargs):
        """Create a volume transfer.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-a-volume-transfer
        """
        post_body = json.dumps({'transfer': kwargs})
        resp, body = self.post('os-volume-transfer', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_volume_transfer, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume_transfer(self, transfer_id):
        """Returns the details of a volume transfer."""
        url = "os-volume-transfer/%s" % transfer_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_volume_transfer, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_volume_transfers(self, detail=False, **params):
        """List all the volume transfers created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-volume-transfers-for-a-project
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#list-volume-transfers-and-details
        """
        url = 'os-volume-transfer'
        schema_list_transfers = schema.list_volume_transfers_no_detail
        if detail:
            url += '/detail'
            schema_list_transfers = schema.list_volume_transfers_with_detail
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema_list_transfers, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_volume_transfer(self, transfer_id):
        """Delete a volume transfer."""
        resp, body = self.delete("os-volume-transfer/%s" % transfer_id)
        self.validate_response(schema.delete_volume_transfer, resp, body)
        return rest_client.ResponseBody(resp, body)

    def accept_volume_transfer(self, transfer_id, **kwargs):
        """Accept a volume transfer.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#accept-a-volume-transfer
        """
        url = 'os-volume-transfer/%s/accept' % transfer_id
        post_body = json.dumps({'accept': kwargs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.accept_volume_transfer, resp, body)
        return rest_client.ResponseBody(resp, body)
