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

import six
from six.moves import http_client as httplib
from six.moves.urllib import parse as urlparse

from tempest.lib.common import rest_client
from tempest.lib import exceptions


class ObjectClient(rest_client.RestClient):

    def create_object(self, container, object_name, data,
                      params=None, metadata=None, headers=None):
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

        resp, body = self.put(url, data, headers)
        self.expected_success(201, resp.status)
        return resp, body

    def update_object(self, container, object_name, data):
        """Upload data to replace current storage object."""
        resp, body = self.create_object(container, object_name, data)
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

    def update_object_metadata(self, container, object_name, metadata,
                               metadata_prefix='X-Object-Meta-'):
        """Add, remove, or change X-Object-Meta metadata for storage object."""

        headers = {}
        for key in metadata:
            headers["%s%s" % (str(metadata_prefix), str(key))] = metadata[key]

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.post(url, None, headers=headers)
        self.expected_success(202, resp.status)
        return resp, body

    def list_object_metadata(self, container, object_name):
        """List all storage object X-Object-Meta- metadata."""

        url = "%s/%s" % (str(container), str(object_name))
        resp, body = self.head(url)
        self.expected_success(200, resp.status)
        return resp, body

    def get_object(self, container, object_name, metadata=None):
        """Retrieve object's data."""

        headers = {}
        if metadata:
            for key in metadata:
                headers[str(key)] = metadata[key]

        url = "{0}/{1}".format(container, object_name)
        resp, body = self.get(url, headers=headers)
        self.expected_success([200, 206], resp.status)
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
        self.expected_success(201, resp.status)
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
        self.expected_success(201, resp.status)
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

    def create_object_segments(self, container, object_name, segment, data):
        """Creates object segments."""
        url = "{0}/{1}/{2}".format(container, object_name, segment)
        resp, body = self.put(url, data)
        self.expected_success(201, resp.status)
        return resp, body

    def put_object_with_chunk(self, container, name, contents):
        """Put an object with Transfer-Encoding header

        :param container: name of the container
        :type container: string
        :param name: name of the object
        :type name: string
        :param contents: object data
        :type contents: iterable
        """
        headers = {'Transfer-Encoding': 'chunked'}
        if self.token:
            headers['X-Auth-Token'] = self.token

        url = "%s/%s" % (container, name)
        resp, body = self.put(
            url, headers=headers,
            body=contents,
            chunked=True
        )

        self._error_checker('PUT', None, headers, contents, resp, body)
        self.expected_success(201, resp.status)
        return resp.status, resp.reason, resp

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

        conn = create_connection(parsed)

        # Send the PUT request and the headers including the "Expect" header
        conn.putrequest('PUT', path)

        for header, value in six.iteritems(headers):
            conn.putheader(header, value)
        conn.endheaders()

        # Read the 100 status prior to sending the data
        response = conn.response_class(conn.sock,
                                       strict=conn.strict,
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


def create_connection(parsed_url):
    """Helper function to create connection with httplib

    :param parsed_url: parsed url of the remote location
    """
    if parsed_url.scheme == 'https':
        conn = httplib.HTTPSConnection(parsed_url.netloc)
    else:
        conn = httplib.HTTPConnection(parsed_url.netloc)

    return conn


def put_object_connection(base_url, container, name, contents=None,
                          chunk_size=65536, headers=None, query_string=None):
    """Helper function to make connection to put object with httplib

    :param base_url: base_url of an object client
    :param container: container name that the object is in
    :param name: object name to put
    :param contents: a string or a file like object to read object data
                     from; if None, a zero-byte put will be done
    :param chunk_size: chunk size of data to write; it defaults to 65536;
                       used only if the contents object has a 'read'
                       method, eg. file-like objects, ignored otherwise
    :param headers: additional headers to include in the request, if any
    :param query_string: if set will be appended with '?' to generated path
    """
    parsed = urlparse.urlparse(base_url)

    path = str(parsed.path) + "/"
    path += "%s/%s" % (str(container), str(name))

    conn = create_connection(parsed)

    if query_string:
        path += '?' + query_string
    if headers:
        headers = dict(headers)
    else:
        headers = {}

    conn.request('PUT', path, contents, headers)

    return conn
