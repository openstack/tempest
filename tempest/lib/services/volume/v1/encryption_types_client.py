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
from tempest.lib import exceptions as lib_exc


class EncryptionTypesClient(rest_client.RestClient):

    def is_resource_deleted(self, id):
        try:
            body = self.show_encryption_type(id)
            if not body:
                return True
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'encryption-type'

    def show_encryption_type(self, volume_type_id):
        """Get the volume encryption type for the specified volume type.

        :param volume_type_id: Id of volume type.
        """
        url = "/types/%s/encryption" % volume_type_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_encryption_type(self, volume_type_id, **kwargs):
        """Create encryption type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v2/#create-an-encryption-type-for-v2
        """
        url = "/types/%s/encryption" % volume_type_id
        post_body = json.dumps({'encryption': kwargs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_encryption_type(self, volume_type_id):
        """Delete the encryption type for the specified volume type."""
        resp, body = self.delete(
            "/types/%s/encryption/provider" % volume_type_id)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)
