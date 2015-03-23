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

import json
import urllib

import jsonschema
from tempest_lib import exceptions as lib_exc

from tempest.common import glance_http
from tempest.common import service_client


class ImageClientV2JSON(service_client.ServiceClient):

    def __init__(self, auth_provider, catalog_type, region, endpoint_type=None,
                 build_interval=None, build_timeout=None,
                 disable_ssl_certificate_validation=None, ca_certs=None,
                 trace_requests=None):
        super(ImageClientV2JSON, self).__init__(
            auth_provider,
            catalog_type,
            region,
            endpoint_type=endpoint_type,
            build_interval=build_interval,
            build_timeout=build_timeout,
            disable_ssl_certificate_validation=(
                disable_ssl_certificate_validation),
            ca_certs=ca_certs,
            trace_requests=trace_requests)
        self._http = None
        self.dscv = disable_ssl_certificate_validation
        self.ca_certs = ca_certs

    def _get_http(self):
        return glance_http.HTTPClient(auth_provider=self.auth_provider,
                                      filters=self.filters,
                                      insecure=self.dscv,
                                      ca_certs=self.ca_certs)

    def _validate_schema(self, body, type='image'):
        if type in ['image', 'images']:
            schema = self.get_schema(type)
        else:
            raise ValueError("%s is not a valid schema type" % type)

        jsonschema.validate(body, schema)

    @property
    def http(self):
        if self._http is None:
            self._http = self._get_http()
        return self._http

    def update_image(self, image_id, patch):
        data = json.dumps(patch)
        self._validate_schema(data)

        headers = {"Content-Type": "application/openstack-images-v2.0"
                                   "-json-patch"}
        resp, body = self.patch('v2/images/%s' % image_id, data, headers)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, self._parse_resp(body))

    def create_image(self, name, container_format, disk_format, **kwargs):
        params = {
            "name": name,
            "container_format": container_format,
            "disk_format": disk_format,
        }

        for option in kwargs:
            value = kwargs.get(option)
            if isinstance(value, dict) or isinstance(value, tuple):
                params.update(value)
            else:
                params[option] = value

        data = json.dumps(params)
        self._validate_schema(data)

        resp, body = self.post('v2/images', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        url = 'v2/images/%s' % image_id
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def image_list(self, params=None):
        url = 'v2/images'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        self._validate_schema(body, type='images')
        return service_client.ResponseBodyList(resp, body['images'])

    def get_image(self, image_id):
        url = 'v2/images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
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

    def store_image(self, image_id, data):
        url = 'v2/images/%s/file' % image_id
        headers = {'Content-Type': 'application/octet-stream'}
        resp, body = self.http.raw_request('PUT', url, headers=headers,
                                           body=data)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def get_image_file(self, image_id):
        url = 'v2/images/%s/file' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBodyData(resp, body)

    def add_image_tag(self, image_id, tag):
        url = 'v2/images/%s/tags/%s' % (image_id, tag)
        resp, body = self.put(url, body=None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def delete_image_tag(self, image_id, tag):
        url = 'v2/images/%s/tags/%s' % (image_id, tag)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def get_image_membership(self, image_id):
        url = 'v2/images/%s/members' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def add_member(self, image_id, member_id):
        url = 'v2/images/%s/members' % image_id
        data = json.dumps({'member': member_id})
        resp, body = self.post(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def update_member_status(self, image_id, member_id, status):
        """Valid status are: ``pending``, ``accepted``,  ``rejected``."""
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        data = json.dumps({'status': status})
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def get_member(self, image_id, member_id):
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, json.loads(body))

    def remove_member(self, image_id, member_id):
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def get_schema(self, schema):
        url = 'v2/schemas/%s' % schema
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)
