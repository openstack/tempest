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

import urllib

from tempest.common import http
from tempest.common.rest_client import RestClient
from tempest import config
from tempest import exceptions

CONF = config.CONF


class ObjectClient(RestClient):
    def __init__(self, auth_provider):
        super(ObjectClient, self).__init__(auth_provider)

        self.service = CONF.object_storage.catalog_type

    def create_object(self, container, object_name, data, params=None):
        """Create storage object."""

        headers = self.get_headers()
        if not data:
            headers['content-length'] = '0'
        url = "%s/%s" % (str(container), str(object_name))
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.put(url, data, headers)
        return resp, body

    def update_object(self, container, object_name, data):
        """Upload data to replace current storage object."""
        return self.create_object(container, object_name, data)

    def delete_object(self, container, object_name, params=None):
        """Delete storage object."""
        url = "%s/%s" % (str(container), str(object_name))
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.delete(url, headers={})
        return resp, body

    def update_object_metadata(self, container, object_name, metadata,
                               metadata_prefix='X-Object-Meta-'):
        """Add, remove, or change X-Object-Meta metadata for storage object."""

        headers = {}
        for key in metadata:
            headers["%s%s" % (str(metadata_prefix), str(key))] = metadata[key]

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.post(url, None, headers=headers)
        return resp, body

    def list_object_metadata(self, container, object_name):
        """List all storage object X-Object-Meta- metadata."""

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.head(url)
        return resp, body

    def get_object(self, container, object_name):
        """Retrieve object's data."""

        url = "{0}/{1}".format(container, object_name)
        resp, body = self.get(url)
        return resp, body

    def copy_object_in_same_container(self, container, src_object_name,
                                      dest_object_name, metadata=None):
        """Copy storage object's data to the new object using PUT."""

        url = "{0}/{1}".format(container, dest_object_name)
        headers = {}
        headers['X-Copy-From'] = "%s/%s" % (str(container),
                                            str(src_object_name))
        headers['content-length'] = '0'
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        resp, body = self.put(url, None, headers=headers)
        return resp, body

    def copy_object_across_containers(self, src_container, src_object_name,
                                      dst_container, dst_object_name,
                                      metadata=None):
        """Copy storage object's data to the new object using PUT."""

        url = "{0}/{1}".format(dst_container, dst_object_name)
        headers = {}
        headers['X-Copy-From'] = "%s/%s" % (str(src_container),
                                            str(src_object_name))
        headers['content-length'] = '0'
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        resp, body = self.put(url, None, headers=headers)
        return resp, body

    def copy_object_2d_way(self, container, src_object_name, dest_object_name,
                           metadata=None):
        """Copy storage object's data to the new object using COPY."""

        url = "{0}/{1}".format(container, src_object_name)
        headers = {}
        headers['Destination'] = "%s/%s" % (str(container),
                                            str(dest_object_name))
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        resp, body = self.copy(url, headers=headers)
        return resp, body

    def create_object_segments(self, container, object_name, segment, data):
        """Creates object segments."""
        url = "{0}/{1}/{2}".format(container, object_name, segment)
        resp, body = self.put(url, data)
        return resp, body


class ObjectClientCustomizedHeader(RestClient):

    # TODO(andreaf) This class is now redundant, to be removed in next patch

    def __init__(self, auth_provider):
        super(ObjectClientCustomizedHeader, self).__init__(
            auth_provider)
        # Overwrites json-specific header encoding in RestClient
        self.service = CONF.object_storage.catalog_type
        self.format = 'json'

    def request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        dscv = CONF.identity.disable_ssl_certificate_validation
        self.http_obj = http.ClosingHttp(
            disable_ssl_certificate_validation=dscv)
        if headers is None:
            headers = {}

        # Authorize the request
        req_url, req_headers, req_body = self.auth_provider.auth_request(
            method=method, url=url, headers=headers, body=body,
            filters=self.filters
        )
        # Use original method
        self._log_request(method, req_url, headers, body)
        resp, resp_body = self.http_obj.request(req_url, method,
                                                headers=req_headers,
                                                body=req_body)
        self._log_response(resp, resp_body)
        if resp.status == 401 or resp.status == 403:
            raise exceptions.Unauthorized()

        return resp, resp_body

    def get_object(self, container, object_name, metadata=None):
        """Retrieve object's data."""
        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        url = "{0}/{1}".format(container, object_name)
        resp, body = self.get(url, headers=headers)
        return resp, body

    def create_object(self, container, object_name, data, metadata=None):
        """Create storage object."""

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        if not data:
            headers['content-length'] = '0'
        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.put(url, data, headers=headers)
        return resp, body

    def delete_object(self, container, object_name, metadata=None):
        """Delete storage object."""

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.delete(url, headers=headers)
        return resp, body
