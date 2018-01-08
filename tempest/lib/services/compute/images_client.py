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

from tempest.lib.api_schema.response.compute.v2_1 import images as schema
from tempest.lib.api_schema.response.compute.v2_45 import images as schemav245
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import base_compute_client


class ImagesClient(base_compute_client.BaseComputeClient):

    schema_versions_info = [
        {'min': None, 'max': '2.44', 'schema': schema},
        {'min': '2.45', 'max': None, 'schema': schemav245}]

    def create_image(self, server_id, **kwargs):
        """Create an image of the original server.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-image-createimage-action
        """

        post_body = {'createImage': kwargs}
        post_body = json.dumps(post_body)
        resp, body = self.post('servers/%s/action' % server_id,
                               post_body)
        _schema = self.get_schema(self.schema_versions_info)
        if body:
            body = json.loads(body)
        self.validate_response(_schema.create_image, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_images(self, detail=False, **params):
        """Return a list of all images filtered by any parameter.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#list-images
        https://developer.openstack.org/api-ref/compute/#list-images-with-details
        """
        url = 'images'
        _schema = schema.list_images
        if detail:
            url += '/detail'
            _schema = schema.list_images_details

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(_schema, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        """Return the details of a single image."""
        resp, body = self.get("images/%s" % image_id)
        body = json.loads(body)
        self.validate_response(schema.get_image, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        """Delete the provided image."""
        resp, body = self.delete("images/%s" % image_id)
        self.validate_response(schema.delete, resp, body)
        return rest_client.ResponseBody(resp, body)

    def list_image_metadata(self, image_id):
        """List all metadata items for an image."""
        resp, body = self.get("images/%s/metadata" % image_id)
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_image_metadata(self, image_id, meta):
        """Set the metadata for an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#update-image-metadata
        """
        post_body = json.dumps({'metadata': meta})
        resp, body = self.put('images/%s/metadata' % image_id, post_body)
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_image_metadata(self, image_id, meta):
        """Update the metadata for an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-image-metadata
        """
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('images/%s/metadata' % image_id, post_body)
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_image_metadata_item(self, image_id, key):
        """Return the value for a specific image metadata key."""
        resp, body = self.get("images/%s/metadata/%s" % (image_id, key))
        body = json.loads(body)
        self.validate_response(schema.image_meta_item, resp, body)
        return rest_client.ResponseBody(resp, body)

    def set_image_metadata_item(self, image_id, key, meta):
        """Set the value for a specific image metadata key.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/compute/#create-or-update-image-metadata-item
        """
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('images/%s/metadata/%s' % (image_id, key),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.image_meta_item, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_image_metadata_item(self, image_id, key):
        """Delete a single image metadata key/value pair."""
        resp, body = self.delete("images/%s/metadata/%s" %
                                 (image_id, key))
        self.validate_response(schema.delete, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        # Added status check for user with admin role
        try:
            if self.show_image(id)['image']['status'] == 'DELETED':
                return True
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'image'
