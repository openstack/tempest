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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.compute.v2_1 import volumes as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import base_compute_client


class VolumesClient(base_compute_client.BaseComputeClient):

    def list_volumes(self, detail=False, **params):
        """List all the volumes created.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-volumes
        https://docs.openstack.org/api-ref/compute/#list-volumes-with-details
        """
        url = 'os-volumes'

        if detail:
            url += '/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_volumes, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_volume(self, volume_id):
        """Return the details of a single volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#show-volume-details
        """
        url = "os-volumes/%s" % volume_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.create_get_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_volume(self, **kwargs):
        """Create a new Volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-volume
        """
        post_body = json.dumps({'volume': kwargs})
        resp, body = self.post('os-volumes', post_body)
        body = json.loads(body)
        self.validate_response(schema.create_get_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_volume(self, volume_id):
        """Delete the Specified Volume.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-volume
        """
        resp, body = self.delete("os-volumes/%s" % volume_id)
        self.validate_response(schema.delete_volume, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_volume(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'volume'
