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
import ssl

from http import client as httplib
from urllib import parse as urlparse

from tempest.lib.common import rest_client
from tempest.lib import exceptions


class ObjectClient(rest_client.RestClient):

    def is_resource_deleted(self, object_name, container):
        try:
            self.get_object(container, object_name)
        except exceptions.NotFound:
            return True
        except exceptions.Conflict:
            return False
        return False

    def create_object(self, container, object_name, data,
                      params=None, metadata=None, headers=None,
                      chunked=False):
        """Create storage object."""

        if headers is None:
            headers = self.get_headers()
        if not data:
            headers['content-length'] = '0'
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]
        url = "%s/%s" % (str(container), str(object_name))
        if params:
            url += '?%s' % urlparse.urlencode(params)

        resp, body = self.put(url, data, headers, chunked=chunked)
        self.expected_success(201, resp.status)
        return resp, body

    def delete_object(self, container, object_name, params=None):
        """Delete storage object."""
        url = "%s/%s" % (str(container), str(object_name))
        if params:
            url += '?%s' % urlparse.urlencode(params)
        resp, body = self.delete(url, headers={})
        self.expected_success([200, 204], resp.status)
        return resp, body

    def create_or_update_object_metadata(self, container, object_name,
                                         headers=None):
        """Add, remove, or change X-Object-Meta metadata for storage object."""

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.post(url, None, headers=headers)
        self.expected_success(202, resp.status)
        return resp, body

    def list_object_metadata(self, container, object_name,
                             params=None, headers=None):
        """List all storage object X-Object-Meta- metadata."""

        url = "%s/%s" % (str(container), str(object_name))
        if params:
            url += '?%s' % urlparse.urlencode(params)
        resp, body = self.head(url, headers=headers)
        self.expected_success(200, resp.status)
        return resp, body

    def get_object(self, container, object_name, metadata=None, params=None):
        """Retrieve object's data."""

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        url = "{0}/{1}".format(container, object_name)
        if params:
            url += '?%s' % urlparse.urlencode(params)
        resp, body = self.get(url, headers=headers)
        self.expected_success([200, 206], resp.status)
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
        self.expected_success(201, resp.status)
        return resp, body

    def create_object_continue(self, container, object_name,
                               data, metadata=None):
        """Put an object using Expect:100-continue"""
        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        headers['X-Auth-Token'] = self.token
        headers['content-length'] = 0 if data is None else len(data)
        headers['Expect'] = '100-continue'

        parsed = urlparse.urlparse(self.base_url)
        path = str(parsed.path) + "/"
        path += "%s/%s" % (str(container), str(object_name))

        conn = self._create_connection(parsed)
        # Send the PUT request and the headers including the "Expect" header
        conn.putrequest('PUT', path)

        for header, value in headers.items():
            conn.putheader(header, value)
        conn.endheaders()

        # Read the 100 status prior to sending the data
        response = conn.response_class(conn.sock,
                                       method=conn._method)
        _, status, _ = response._read_status()

        # toss the CRLF at the end of the response
        response._safe_read(2)

        # Expecting a 100 here, if not close and throw an exception
        if status != 100:
            conn.close()
            pattern = "%s %s" % (
                """Unexpected http success status code {0}.""",
                """The expected status code is {1}""")
            details = pattern.format(status, 100)
            raise exceptions.UnexpectedResponseCode(details)

        # If a continue was received go ahead and send the data
        # and get the final response
        conn.send(data)

        resp = conn.getresponse()

        return resp.status, resp.reason

    def _create_connection(self, parsed_url):
        """Helper function to create connection with httplib

        :param parsed_url: parsed url of the remote location
        """
        context = None
        # If CONF.identity.disable_ssl_certificate_validation is true,
        # do not check ssl certification.
        if self.dscv:
            context = ssl._create_unverified_context()
        if parsed_url.scheme == 'https':
            conn = httplib.HTTPSConnection(parsed_url.netloc,
                                           context=context)
        else:
            conn = httplib.HTTPConnection(parsed_url.netloc)

        return conn
