# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 NTT Corporation
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

import re


class ExistsAllResponseHeaders(object):
    """
    Specific matcher to check the existence of Swift's response headers

    This matcher checks the existence of common headers for each HTTP method
    or the target, which means account, container or object.
    When checking the existence of 'specific' headers such as
    X-Account-Meta-* or X-Object-Manifest for example, those headers must be
    checked in each test code.
    """

    def __init__(self, target, method):
        """
        param: target Account/Container/Object
        param: method PUT/GET/HEAD/DELETE/COPY/POST
        """
        self.target = target
        self.method = method

    def match(self, actual):
        """
        param: actual HTTP response headers
        """
        # Check common headers for all HTTP methods
        if 'content-length' not in actual:
            return NonExistentHeader('content-length')
        if 'content-type' not in actual:
            return NonExistentHeader('content-type')
        if 'x-trans-id' not in actual:
            return NonExistentHeader('x-trans-id')
        if 'date' not in actual:
            return NonExistentHeader('date')

        # Check headers for a specific method or target
        if self.method == 'GET' or self.method == 'HEAD':
            if 'x-timestamp' not in actual:
                return NonExistentHeader('x-timestamp')
            if 'accept-ranges' not in actual:
                return NonExistentHeader('accept-ranges')
            if self.target == 'Account':
                if 'x-account-bytes-used' not in actual:
                    return NonExistentHeader('x-account-bytes-used')
                if 'x-account-container-count' not in actual:
                    return NonExistentHeader('x-account-container-count')
                if 'x-account-object-count' not in actual:
                    return NonExistentHeader('x-account-object-count')
            elif self.target == 'Container':
                if 'x-container-bytes-used' not in actual:
                    return NonExistentHeader('x-container-bytes-used')
                if 'x-container-object-count' not in actual:
                    return NonExistentHeader('x-container-object-count')
            elif self.target == 'Object':
                if 'etag' not in actual:
                    return NonExistentHeader('etag')
        elif self.method == 'PUT' or self.method == 'COPY':
            if self.target == 'Object':
                if 'etag' not in actual:
                    return NonExistentHeader('etag')

        return None


class NonExistentHeader(object):
    """
    Informs an error message for end users in the case of missing a
    certain header in Swift's responses
    """

    def __init__(self, header):
        self.header = header

    def describe(self):
        return "%s header does not exist" % self.header

    def get_details(self):
        return {}


class AreAllWellFormatted(object):
    """
    Specific matcher to check the correctness of formats of values of Swift's
    response headers

    This matcher checks the format of values of response headers.
    When checking the format of values of 'specific' headers such as
    X-Account-Meta-* or X-Object-Manifest for example, those values must be
    checked in each test code.
    """

    def match(self, actual):
        for key, value in actual.iteritems():
            if key == 'content-length' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'x-timestamp' and not re.match("^\d+\.?\d*\Z", value):
                return InvalidFormat(key, value)
            elif key == 'x-account-bytes-used' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'x-account-container-count' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'x-account-object-count' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'x-container-bytes-used' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'x-container-object-count' and not value.isdigit():
                return InvalidFormat(key, value)
            elif key == 'content-type' and not value:
                return InvalidFormat(key, value)
            elif key == 'x-trans-id' and \
                not re.match("^tx[0-9a-f]{21}-[0-9a-f]{10}.*", value):
                return InvalidFormat(key, value)
            elif key == 'date' and not value:
                return InvalidFormat(key, value)
            elif key == 'accept-ranges' and not value == 'bytes':
                return InvalidFormat(key, value)
            elif key == 'etag' and not value.isalnum():
                return InvalidFormat(key, value)

        return None


class InvalidFormat(object):
    """
    Informs an error message for end users if a format of a certain header
    is invalid
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def describe(self):
        return "InvalidFormat (%s, %s)" % (self.key, self.value)

    def get_details(self):
        return {}
