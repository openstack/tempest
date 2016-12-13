# Copyright 2013 IBM Corp.
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

import functools

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc

CHUNKSIZE = 1024 * 64  # 64kB


class ImagesClient(rest_client.RestClient):
    api_version = "v2"

    def update_image(self, image_id, patch):
        """Update an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#updateImage-v2
        """
        data = json.dumps(patch)
        headers = {"Content-Type": "application/openstack-images-v2.0"
                                   "-json-patch"}
        resp, body = self.patch('images/%s' % image_id, data, headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_image(self, **kwargs):
        """Create an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#createImage-v2
        """
        data = json.dumps(kwargs)
        resp, body = self.post('images', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def deactivate_image(self, image_id):
        """Deactivate image.

         Available params: see http://developer.openstack.org/
                               api-ref-image-v2.html#deactivateImage-v2
         """
        url = 'images/%s/actions/deactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reactivate_image(self, image_id):
        """Reactivate image.

         Available params: see http://developer.openstack.org/
                               api-ref-image-v2.html#reactivateImage-v2
         """
        url = 'images/%s/actions/reactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        """Delete image.

         Available params: see http://developer.openstack.org/
                               api-ref-image-v2.html#deleteImage-v2
         """
        url = 'images/%s' % image_id
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_images(self, params=None):
        """List images.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#listImages-v2
        """
        url = 'images'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        """Show image details.

        Available params: http://developer.openstack.org/
                          api-ref-image-v2.html#showImage-v2
        """
        url = 'images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_image(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'image'

    def store_image_file(self, image_id, data):
        """Upload binary image data.

        Available params: http://developer.openstack.org/
                          api-ref-image-v2.html#storeImageFile-v2
        """
        url = 'images/%s/file' % image_id

        # We are going to do chunked transfert, so split the input data
        # info fixed-sized chunks.
        headers = {'Content-Type': 'application/octet-stream'}
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')

        resp, body = self.request('PUT', url, headers=headers,
                                  body=data, chunked=True)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_image_file(self, image_id):
        """Download binary image data.

        Available params: http://developer.openstack.org/
                          api-ref-image-v2.html#showImageFile-v2
        """
        url = 'images/%s/file' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def add_image_tag(self, image_id, tag):
        """Add an image tag.

        Available params: http://developer.openstack.org/
                          api-ref-image-v2.html#addImageTag-v2
        """
        url = 'images/%s/tags/%s' % (image_id, tag)
        resp, body = self.put(url, body=None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image_tag(self, image_id, tag):
        """Delete an image tag.

        Available params: http://developer.openstack.org/
                          api-ref-image-v2.html#deleteImageTag-v2
        """
        url = 'images/%s/tags/%s' % (image_id, tag)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
