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

import json
import urllib

from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import images as schema
from tempest.common import service_client
from tempest.common import waiters


class ImagesClientJSON(service_client.ServiceClient):

    def create_image(self, server_id, name, meta=None):
        """Creates an image of the original server."""

        post_body = {
            'createImage': {
                'name': name,
            }
        }

        if meta is not None:
            post_body['createImage']['metadata'] = meta

        post_body = json.dumps(post_body)
        resp, body = self.post('servers/%s/action' % str(server_id),
                               post_body)
        self.validate_response(schema.create_image, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_images(self, params=None):
        """Returns a list of all images filtered by any parameters."""
        url = 'images'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_images, resp, body)
        return service_client.ResponseBodyList(resp, body['images'])

    def list_images_with_detail(self, params=None):
        """Returns a detailed list of images filtered by any parameters."""
        url = 'images/detail'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_images_details, resp, body)
        return service_client.ResponseBodyList(resp, body['images'])

    def get_image(self, image_id):
        """Returns the details of a single image."""
        resp, body = self.get("images/%s" % str(image_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        self.validate_response(schema.get_image, resp, body)
        return service_client.ResponseBody(resp, body['image'])

    def delete_image(self, image_id):
        """Deletes the provided image."""
        resp, body = self.delete("images/%s" % str(image_id))
        self.validate_response(schema.delete, resp, body)
        return service_client.ResponseBody(resp, body)

    def wait_for_image_status(self, image_id, status):
        """Waits for an image to reach a given status."""
        waiters.wait_for_image_status(self, image_id, status)

    def list_image_metadata(self, image_id):
        """Lists all metadata items for an image."""
        resp, body = self.get("images/%s/metadata" % str(image_id))
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return service_client.ResponseBody(resp, body['metadata'])

    def set_image_metadata(self, image_id, meta):
        """Sets the metadata for an image."""
        post_body = json.dumps({'metadata': meta})
        resp, body = self.put('images/%s/metadata' % str(image_id), post_body)
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return service_client.ResponseBody(resp, body['metadata'])

    def update_image_metadata(self, image_id, meta):
        """Updates the metadata for an image."""
        post_body = json.dumps({'metadata': meta})
        resp, body = self.post('images/%s/metadata' % str(image_id), post_body)
        body = json.loads(body)
        self.validate_response(schema.image_metadata, resp, body)
        return service_client.ResponseBody(resp, body['metadata'])

    def get_image_metadata_item(self, image_id, key):
        """Returns the value for a specific image metadata key."""
        resp, body = self.get("images/%s/metadata/%s" % (str(image_id), key))
        body = json.loads(body)
        self.validate_response(schema.image_meta_item, resp, body)
        return service_client.ResponseBody(resp, body['meta'])

    def set_image_metadata_item(self, image_id, key, meta):
        """Sets the value for a specific image metadata key."""
        post_body = json.dumps({'meta': meta})
        resp, body = self.put('images/%s/metadata/%s' % (str(image_id), key),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.image_meta_item, resp, body)
        return service_client.ResponseBody(resp, body['meta'])

    def delete_image_metadata_item(self, image_id, key):
        """Deletes a single image metadata key/value pair."""
        resp, body = self.delete("images/%s/metadata/%s" %
                                 (str(image_id), key))
        self.validate_response(schema.delete, resp, body)
        return service_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.get_image(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'image'
