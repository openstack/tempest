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

from tempest.lib.api_schema.response.volume import encryption_types as schema
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
        self.validate_response(schema.show_encryption_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_encryption_specs_item(self, volume_type_id, key):
        """Get the encryption specs item for the specified volume type."""
        url = "/types/%s/encryption/%s" % (volume_type_id, key)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.show_encryption_specs_item, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_encryption_type(self, volume_type_id, **kwargs):
        """Create encryption type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#create-an-encryption-type
        """
        url = "/types/%s/encryption" % volume_type_id
        post_body = json.dumps({'encryption': kwargs})
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_encryption_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_encryption_type(self, volume_type_id, encryption_id):
        """Delete the encryption type for the specified volume-type."""
        resp, body = self.delete(
            "/types/%s/encryption/%s" % (volume_type_id, encryption_id))
        self.validate_response(schema.delete_encryption_type, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_encryption_type(self, volume_type_id, encryption_id, **kwargs):
        """Update an encryption type for an existing volume type.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/block-storage/v3/index.html#update-an-encryption-type
        """
        url = "/types/%s/encryption/%s" % (volume_type_id, encryption_id)
        put_body = json.dumps({'encryption': kwargs})
        resp, body = self.put(url, put_body)
        body = json.loads(body)
        self.validate_response(schema.update_encryption_type, resp, body)
        return rest_client.ResponseBody(resp, body)
