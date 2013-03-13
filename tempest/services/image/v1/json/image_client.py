# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 IBM
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
import errno
import json
import os
import urllib

from tempest.common import glance_http
from tempest.common.rest_client import RestClient
from tempest import exceptions


class ImageClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(ImageClientJSON, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.images.catalog_type
        self.http = self._get_http()

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        for key, value in headers.iteritems():
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
        for key, value in fields_copy.pop('properties', {}).iteritems():
            headers['x-image-meta-property-%s' % key] = str(value)
        for key, value in fields_copy.iteritems():
            headers['x-image-meta-%s' % key] = str(value)
        return headers

    def _get_file_size(self, obj):
        """Analyze file-like object and attempt to determine its size.

        :param obj: file-like object, typically redirected from stdin.
        :retval The file's size or None if it cannot be determined.
        """
        # For large images, we need to supply the size of the
        # image file. See LP Bugs #827660 and #845788.
        if hasattr(obj, 'seek') and hasattr(obj, 'tell'):
            try:
                obj.seek(0, os.SEEK_END)
                obj_size = obj.tell()
                obj.seek(0)
                return obj_size
            except IOError, e:
                if e.errno == errno.ESPIPE:
                    # Illegal seek. This means the user is trying
                    # to pipe image data to the client, e.g.
                    # echo testdata | bin/glance add blah..., or
                    # that stdin is empty, or that a file-like
                    # object which doesn't support 'seek/tell' has
                    # been supplied.
                    return None
                else:
                    raise
        else:
            # Cannot determine size of input image
            return None

    def _get_http(self):
        token, endpoint = self.keystone_auth(self.user,
                                             self.password,
                                             self.auth_url,
                                             self.service,
                                             self.tenant_name)
        dscv = self.config.identity.disable_ssl_certificate_validation
        return glance_http.HTTPClient(endpoint=endpoint, token=token,
                                      insecure=dscv)

    def _create_with_data(self, headers, data):
        resp, body_iter = self.http.raw_request('POST', '/v1/images',
                                                headers=headers, body=data)
        self._error_checker('POST', '/v1/images', headers, data, resp,
                            body_iter)
        body = json.loads(''.join([c for c in body_iter]))
        return resp, body['image']

    def _update_with_data(self, image_id, headers, data):
        url = '/v1/images/%s' % image_id
        resp, body_iter = self.http.raw_request('PUT', url, headers=headers,
                                                body=data)
        self._error_checker('PUT', url, headers, data,
                            resp, body_iter)
        body = json.loads(''.join([c for c in body_iter]))
        return resp, body['image']

    def create_image(self, name, container_format, disk_format, **kwargs):
        params = {
            "name": name,
            "container_format": container_format,
            "disk_format": disk_format,
        }

        headers = {}

        for option in ['is_public', 'location', 'properties']:
            if option in kwargs:
                params[option] = kwargs.get(option)

        headers.update(self._image_meta_to_headers(params))

        if 'data' in kwargs:
            return self._create_with_data(headers, kwargs.get('data'))

        resp, body = self.post('v1/images', None, headers)
        body = json.loads(body)
        return resp, body['image']

    def update_image(self, image_id, name=None, container_format=None,
                     data=None):
        params = {}
        headers = {}
        if name is not None:
            params['name'] = name

        if container_format is not None:
            params['container_format'] = container_format

        headers.update(self._image_meta_to_headers(params))

        if data is not None:
            return self._update_with_data(image_id, headers, data)

        url = 'v1/images/%s' % image_id
        resp, body = self.put(url, data, headers)
        body = json.loads(body)
        return resp, body['image']

    def delete_image(self, image_id):
        url = 'v1/images/%s' % image_id
        self.delete(url)

    def image_list(self, **kwargs):
        url = 'v1/images'

        if len(kwargs) > 0:
            url += '?%s' % urllib.urlencode(kwargs)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['images']

    def image_list_detail(self, **kwargs):
        url = 'v1/images/detail'

        if len(kwargs) > 0:
            url += '?%s' % urllib.urlencode(kwargs)

        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['images']

    def get_image(self, image_id):
        url = 'v1/images/%s' % image_id
        resp, __ = self.get(url)
        body = self._image_meta_from_headers(resp)
        return resp, body

    def is_resource_deleted(self, id):
        try:
            self.get_image(id)
        except exceptions.NotFound:
            return True
        return False

    def get_image_membership(self, image_id):
        url = 'v1/images/%s/members' % image_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def get_shared_images(self, member_id):
        url = 'v1/shared-images/%s' % member_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body

    def add_member(self, member_id, image_id, can_share=False):
        url = 'v1/images/%s/members/%s' % (image_id, member_id)
        body = None
        if can_share:
            body = json.dumps({'member': {'can_share': True}})
        resp, __ = self.put(url, body, self.headers)
        return resp

    def delete_member(self, member_id, image_id):
        url = 'v1/images/%s/members/%s' % (image_id, member_id)
        resp, __ = self.delete(url)
        return resp

    def replace_membership_list(self, image_id, member_list):
        url = 'v1/images/%s/members' % image_id
        body = json.dumps({'membership': member_list})
        resp, data = self.put(url, body, self.headers)
        data = json.loads(data)
        return resp, data
