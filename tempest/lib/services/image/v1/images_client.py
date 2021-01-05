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
from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc

CHUNKSIZE = 1024 * 64  # 64kB


class ImagesClient(rest_client.RestClient):
    api_version = "v1"

    def _create_with_data(self, headers, data):
        # We are going to do chunked transfert, so split the input data
        # info fixed-sized chunks.
        headers['Content-Type'] = 'application/octet-stream'
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')
        resp, body = self.request('POST', 'images',
                                  headers=headers, body=data, chunked=True)
        self._error_checker(resp, body)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def _update_with_data(self, image_id, headers, data):
        # We are going to do chunked transfert, so split the input data
        # info fixed-sized chunks.
        headers['Content-Type'] = 'application/octet-stream'
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')
        url = 'images/%s' % image_id
        resp, body = self.request('PUT', url, headers=headers,
                                  body=data, chunked=True)
        self._error_checker(resp, body)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    @property
    def http(self):
        if self._http is None:
            self._http = self._get_http()
        return self._http

    def create_image(self, data=None, headers=None):
        """Create an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v1/index.html#create-image
        """
        if headers is None:
            headers = {}

        if data is not None:
            return self._create_with_data(headers, data)

        resp, body = self.post('images', None, headers)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_image(self, image_id, data=None, headers=None):
        """Update an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v1/index.html#update-image
        """
        if headers is None:
            headers = {}

        if data is not None:
            return self._update_with_data(image_id, headers, data)

        url = 'images/%s' % image_id
        resp, body = self.put(url, None, headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        url = 'images/%s' % image_id
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_images(self, detail=False, **kwargs):
        """Return a list of all images filtered by input parameters.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v1/#list-images

        Most parameters except the following are passed to the API without
        any changes.
        :param changes_since: The name is changed to changes-since
        """
        url = 'images'

        if detail:
            url += '/detail'

        if 'changes_since' in kwargs:
            kwargs['changes-since'] = kwargs.pop('changes_since')

        if kwargs:
            url += '?%s' % urllib.urlencode(kwargs)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_image(self, image_id):
        """Check image metadata."""
        url = 'images/%s' % image_id
        resp, body = self.head(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        """Get image details plus the image itself."""
        url = 'images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def is_resource_deleted(self, id):
        try:
            resp = self.check_image(id)
            if resp.response["x-image-meta-status"] == 'deleted':
                return True
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'image_meta'
