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

import copy
import functools

from oslo_log import log as logging
from oslo_serialization import jsonutils as json
import six
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)
CHUNKSIZE = 1024 * 64  # 64kB


class ImagesClient(rest_client.RestClient):

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        for key, value in six.iteritems(headers):
            if key.startswith('x-image-meta-property-'):
                _key = key[22:]
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = key[13:]
                meta[_key] = value

        for key in ['is_public', 'protected', 'deleted']:
            if key in meta:
                meta[key] = meta[key].strip().lower() in ('t', 'true', 'yes',
                                                          '1')
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key])
                except ValueError:
                    pass
        return meta

    def _image_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)
        copy_from = fields_copy.pop('copy_from', None)
        if copy_from is not None:
            headers['x-glance-api-copy-from'] = copy_from
        for key, value in six.iteritems(fields_copy.pop('properties', {})):
            headers['x-image-meta-property-%s' % key] = str(value)
        for key, value in six.iteritems(fields_copy.pop('api', {})):
            headers['x-glance-api-property-%s' % key] = str(value)
        for key, value in six.iteritems(fields_copy):
            headers['x-image-meta-%s' % key] = str(value)
        return headers

    def _create_with_data(self, headers, data):
        # We are going to do chunked transfert, so split the input data
        # info fixed-sized chunks.
        headers['Content-Type'] = 'application/octet-stream'
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')
        resp, body = self.request('POST', '/v1/images',
                                  headers=headers, body=data, chunked=True)
        self._error_checker('POST', '/v1/images', headers, data, resp,
                            body)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def _update_with_data(self, image_id, headers, data):
        # We are going to do chunked transfert, so split the input data
        # info fixed-sized chunks.
        headers['Content-Type'] = 'application/octet-stream'
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')
        url = '/v1/images/%s' % image_id
        resp, body = self.request('PUT', url, headers=headers,
                                  body=data, chunked=True)
        self._error_checker('PUT', url, headers, data,
                            resp, body)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    @property
    def http(self):
        if self._http is None:
            self._http = self._get_http()
        return self._http

    def create_image(self, **kwargs):
        headers = {}
        data = kwargs.pop('data', None)
        headers.update(self._image_meta_to_headers(kwargs))

        if data is not None:
            return self._create_with_data(headers, data)

        resp, body = self.post('v1/images', None, headers)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_image(self, image_id, **kwargs):
        headers = {}
        data = kwargs.pop('data', None)
        headers.update(self._image_meta_to_headers(kwargs))

        if data is not None:
            return self._update_with_data(image_id, headers, data)

        url = 'v1/images/%s' % image_id
        resp, body = self.put(url, None, headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        url = 'v1/images/%s' % image_id
        resp, body = self.delete(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_images(self, detail=False, **kwargs):
        """Return a list of all images filtered by input parameters.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v1.html#listImage-v1

        Most parameters except the following are passed to the API without
        any changes.
        :param changes_since: The name is changed to changes-since
        """
        url = 'v1/images'

        if detail:
            url += '/detail'

        properties = kwargs.pop('properties', {})
        for key, value in six.iteritems(properties):
            kwargs['property-%s' % key] = value

        if kwargs.get('changes_since'):
            kwargs['changes-since'] = kwargs.pop('changes_since')

        if len(kwargs) > 0:
            url += '?%s' % urllib.urlencode(kwargs)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_image(self, image_id):
        """Check image metadata."""
        url = 'v1/images/%s' % image_id
        resp, __ = self.head(url)
        self.expected_success(200, resp.status)
        body = self._image_meta_from_headers(resp)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        """Get image details plus the image itself."""
        url = 'v1/images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def is_resource_deleted(self, id):
        try:
            if self.check_image(id)['status'] == 'deleted':
                return True
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'image_meta'

    def list_image_members(self, image_id):
        url = 'v1/images/%s/members' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_shared_images(self, tenant_id):
        """List shared images with the specified tenant"""
        url = 'v1/shared-images/%s' % tenant_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def add_member(self, member_id, image_id, **kwargs):
        """Add a member to an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v1.html#addMember-v1
        """
        url = 'v1/images/%s/members/%s' % (image_id, member_id)
        body = json.dumps({'member': kwargs})
        resp, __ = self.put(url, body)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def delete_member(self, member_id, image_id):
        url = 'v1/images/%s/members/%s' % (image_id, member_id)
        resp, __ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
