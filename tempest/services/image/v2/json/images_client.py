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

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest.common import glance_http
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc


class ImagesClientV2(rest_client.RestClient):

    def __init__(self, auth_provider, catalog_type, region, **kwargs):
        super(ImagesClientV2, self).__init__(
            auth_provider, catalog_type, region, **kwargs)
        self._http = None
        self.dscv = kwargs.get("disable_ssl_certificate_validation")
        self.ca_certs = kwargs.get("ca_certs")

    def _get_http(self):
        return glance_http.HTTPClient(auth_provider=self.auth_provider,
                                      filters=self.filters,
                                      insecure=self.dscv,
                                      ca_certs=self.ca_certs)

    @property
    def http(self):
        if self._http is None:
            self._http = self._get_http()
        return self._http

    def update_image(self, image_id, patch):
        """Update an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#updateImage-v2
        """
        data = json.dumps(patch)
        headers = {"Content-Type": "application/openstack-images-v2.0"
                                   "-json-patch"}
        resp, body = self.patch('v2/images/%s' % image_id, data, headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_image(self, **kwargs):
        """Create an image.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#createImage-v2
        """
        data = json.dumps(kwargs)
        resp, body = self.post('v2/images', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def deactivate_image(self, image_id):
        url = 'v2/images/%s/actions/deactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reactivate_image(self, image_id):
        url = 'v2/images/%s/actions/reactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        url = 'v2/images/%s' % image_id
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_images(self, params=None):
        url = 'v2/images'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        url = 'v2/images/%s' % image_id
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
        url = 'v2/images/%s/file' % image_id
        headers = {'Content-Type': 'application/octet-stream'}
        resp, body = self.http.raw_request('PUT', url, headers=headers,
                                           body=data)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_image_file(self, image_id):
        url = 'v2/images/%s/file' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def add_image_tag(self, image_id, tag):
        url = 'v2/images/%s/tags/%s' % (image_id, tag)
        resp, body = self.put(url, body=None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image_tag(self, image_id, tag):
        url = 'v2/images/%s/tags/%s' % (image_id, tag)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_image_members(self, image_id):
        url = 'v2/images/%s/members' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_image_member(self, image_id, **kwargs):
        """Create an image member.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#createImageMember-v2
        """
        url = 'v2/images/%s/members' % image_id
        data = json.dumps(kwargs)
        resp, body = self.post(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_image_member(self, image_id, member_id, **kwargs):
        """Update an image member.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#updateImageMember-v2
        """
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        data = json.dumps(kwargs)
        resp, body = self.put(url, data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image_member(self, image_id, member_id):
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, json.loads(body))

    def delete_image_member(self, image_id, member_id):
        url = 'v2/images/%s/members/%s' % (image_id, member_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def show_schema(self, schema):
        url = 'v2/schemas/%s' % schema
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_resource_types(self):
        url = '/v2/metadefs/resource_types'
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_namespace(self, **kwargs):
        """Create a namespace.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#createNamespace-v2
        """
        data = json.dumps(kwargs)
        resp, body = self.post('/v2/metadefs/namespaces', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_namespace(self, namespace):
        url = '/v2/metadefs/namespaces/%s' % namespace
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_namespace(self, namespace, **kwargs):
        """Update a namespace.

        Available params: see http://developer.openstack.org/
                              api-ref-image-v2.html#updateNamespace-v2
        """
        # NOTE: On Glance API, we need to pass namespace on both URI
        # and a request body.
        params = {'namespace': namespace}
        params.update(kwargs)
        data = json.dumps(params)
        url = '/v2/metadefs/namespaces/%s' % namespace
        resp, body = self.put(url, body=data)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_namespace(self, namespace):
        url = '/v2/metadefs/namespaces/%s' % namespace
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
