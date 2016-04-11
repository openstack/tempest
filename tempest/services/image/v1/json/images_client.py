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
import errno
import os
import time

from oslo_log import log as logging
from oslo_serialization import jsonutils as json
import six
from six.moves.urllib import parse as urllib

from tempest.common import glance_http
from tempest import exceptions
from tempest.lib.common import rest_client
from tempest.lib.common.utils import misc as misc_utils
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)


class ImagesClient(rest_client.RestClient):

    def __init__(self, auth_provider, catalog_type, region, **kwargs):
        super(ImagesClient, self).__init__(
            auth_provider, catalog_type, region, **kwargs)
        self._http = None
        self.dscv = kwargs.get("disable_ssl_certificate_validation")
        self.ca_certs = kwargs.get("ca_certs")

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
            except IOError as e:
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
        return glance_http.HTTPClient(auth_provider=self.auth_provider,
                                      filters=self.filters,
                                      insecure=self.dscv,
                                      ca_certs=self.ca_certs)

    def _create_with_data(self, headers, data):
        resp, body_iter = self.http.raw_request('POST', '/v1/images',
                                                headers=headers, body=data)
        self._error_checker('POST', '/v1/images', headers, data, resp,
                            body_iter)
        body = json.loads(''.join([c for c in body_iter]))
        return rest_client.ResponseBody(resp, body)

    def _update_with_data(self, image_id, headers, data):
        url = '/v1/images/%s' % image_id
        resp, body_iter = self.http.raw_request('PUT', url, headers=headers,
                                                body=data)
        self._error_checker('PUT', url, headers, data,
                            resp, body_iter)
        body = json.loads(''.join([c for c in body_iter]))
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

    def get_image_meta(self, image_id):
        url = 'v1/images/%s' % image_id
        resp, __ = self.head(url)
        self.expected_success(200, resp.status)
        body = self._image_meta_from_headers(resp)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        url = 'v1/images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyData(resp, body)

    def is_resource_deleted(self, id):
        try:
            if self.get_image_meta(id)['status'] == 'deleted':
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

    # NOTE(afazekas): just for the wait function
    def _get_image_status(self, image_id):
        meta = self.get_image_meta(image_id)
        status = meta['status']
        return status

    # NOTE(afazkas): Wait reinvented again. It is not in the correct layer
    def wait_for_image_status(self, image_id, status):
        """Waits for a Image to reach a given status."""
        start_time = time.time()
        old_value = value = self._get_image_status(image_id)
        while True:
            dtime = time.time() - start_time
            time.sleep(self.build_interval)
            if value != old_value:
                LOG.info('Value transition from "%s" to "%s"'
                         'in %d second(s).', old_value,
                         value, dtime)
            if value == status:
                return value

            if value == 'killed':
                raise exceptions.ImageKilledException(image_id=image_id,
                                                      status=status)
            if dtime > self.build_timeout:
                message = ('Time Limit Exceeded! (%ds)'
                           'while waiting for %s, '
                           'but we got %s.' %
                           (self.build_timeout, status, value))
                caller = misc_utils.find_test_caller()
                if caller:
                    message = '(%s) %s' % (caller, message)
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)
            old_value = value
            value = self._get_image_status(image_id)
