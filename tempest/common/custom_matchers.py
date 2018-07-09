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

from testtools import helpers


class ExistsAllResponseHeaders(object):
    """Specific matcher to check the existence of Swift's response headers

    This matcher checks the existence of common headers for each HTTP method
    or the target, which means account, container or object.
    When checking the existence of 'specific' headers such as
    X-Account-Meta-* or X-Object-Manifest for example, those headers must be
    checked in each test code.
    """

    def __init__(self, target, method, policies=None):
        """Initialization of ExistsAllResponseHeaders

        param: target Account/Container/Object
        param: method PUT/GET/HEAD/DELETE/COPY/POST
        """
        self.target = target
        self.method = method
        self.policies = policies or []

    def _content_length_required(self, resp):
        # Verify whether given HTTP response must contain content-length.
        # Take into account the exceptions defined in RFC 7230.
        if resp.status in range(100, 200) or resp.status == 204:
            return False

        return True

    def match(self, actual):
        """Check headers

        param: actual HTTP response object containing headers and status
        """
        # Check common headers for all HTTP methods.
        #
        # Please note that for 1xx and 204 responses Content-Length presence
        # is not checked intensionally. According to RFC 7230 a server MUST
        # NOT send the header in such responses. Thus, clients should not
        # depend on this header. However, the standard does not require them
        # to validate the server's behavior. We leverage that to not refuse
        # any implementation violating it like Swift [1] or some versions of
        # Ceph RadosGW [2].
        # [1] https://bugs.launchpad.net/swift/+bug/1537811
        # [2] http://tracker.ceph.com/issues/13582
        if ('content-length' not in actual and
                self._content_length_required(actual)):
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
                if int(actual['x-account-container-count']) > 0:
                    acct_header = "x-account-storage-policy-"
                    matched_policy_count = 0

                    # Loop through the policies and look for account
                    # usage data.  There should be at least 1 set
                    for policy in self.policies:
                        front_header = acct_header + policy['name'].lower()

                        usage_policies = [
                            front_header + '-bytes-used',
                            front_header + '-object-count',
                            front_header + '-container-count'
                        ]

                        # There should be 3 usage values for a give storage
                        # policy in an account bytes, object count, and
                        # container count
                        policy_hdrs = sum(1 for use_hdr in usage_policies
                                          if use_hdr in actual)

                        # If there are less than 3 headers here then 1 is
                        # missing, let's figure out which one and report
                        if policy_hdrs == 3:
                            matched_policy_count = matched_policy_count + 1
                        else:
                            if policy_hdrs > 0 and policy_hdrs < 3:
                                for use_hdr in usage_policies:
                                    if use_hdr not in actual:
                                        return NonExistentHeader(use_hdr)

                    # Only flag an error if actual policies have been read and
                    # no usage has been found
                    if self.policies and matched_policy_count == 0:
                        return GenericError("No storage policy usage headers")

            elif self.target == 'Container':
                if 'x-container-bytes-used' not in actual:
                    return NonExistentHeader('x-container-bytes-used')
                if 'x-container-object-count' not in actual:
                    return NonExistentHeader('x-container-object-count')
                if 'x-storage-policy' not in actual:
                    return NonExistentHeader('x-storage-policy')
                else:
                    policy_name = actual['x-storage-policy']

                    # loop through the policies and ensure that
                    # the value in the container header matches
                    # one of the storage policies
                    for policy in self.policies:
                        if policy['name'] == policy_name:
                            break
                    else:
                        # Ensure that there are actual policies stored
                        if self.policies:
                            return InvalidHeaderValue('x-storage-policy',
                                                      policy_name)
            elif self.target == 'Object':
                if 'etag' not in actual:
                    return NonExistentHeader('etag')
                if 'last-modified' not in actual:
                    return NonExistentHeader('last-modified')
        elif self.method == 'PUT':
            if self.target == 'Object':
                if 'etag' not in actual:
                    return NonExistentHeader('etag')
                if 'last-modified' not in actual:
                    return NonExistentHeader('last-modified')
        elif self.method == 'COPY':
            if self.target == 'Object':
                if 'etag' not in actual:
                    return NonExistentHeader('etag')
                if 'last-modified' not in actual:
                    return NonExistentHeader('last-modified')
                if 'x-copied-from' not in actual:
                    return NonExistentHeader('x-copied-from')
                if 'x-copied-from-last-modified' not in actual:
                    return NonExistentHeader('x-copied-from-last-modified')

        return None


class GenericError(object):
    """Informs an error message of a generic error during header evaluation"""

    def __init__(self, body):
        self.body = body

    def describe(self):
        return "%s" % self.body

    def get_details(self):
        return {}


class NonExistentHeader(object):
    """Informs an error message in the case of missing a certain header"""

    def __init__(self, header):
        self.header = header

    def describe(self):
        return "%s header does not exist" % self.header

    def get_details(self):
        return {}


class InvalidHeaderValue(object):
    """Informs an error message when a header contains a bad value"""

    def __init__(self, header, value):
        self.header = header
        self.value = value

    def describe(self):
        return "InvalidValue (%s, %s)" % (self.header, self.value)

    def get_details(self):
        return {}


class AreAllWellFormatted(object):
    """Specific matcher to check the correctness of formats of values

    This matcher checks the format of values of response headers.
    When checking the format of values of 'specific' headers such as
    X-Account-Meta-* or X-Object-Manifest for example, those values must be
    checked in each test code.
    """

    def match(self, actual):
        for key, value in actual.items():
            if key in ('content-length', 'x-account-bytes-used',
                       'x-account-container-count', 'x-account-object-count',
                       'x-container-bytes-used', 'x-container-object-count')\
                and not value.isdigit():
                return InvalidFormat(key, value)
            elif key in ('content-type', 'date', 'last-modified',
                         'x-copied-from-last-modified') and not value:
                return InvalidFormat(key, value)
            elif key == 'x-timestamp' and not re.match(r"^\d+\.?\d*\Z", value):
                return InvalidFormat(key, value)
            elif key == 'x-copied-from' and not re.match(r"\S+/\S+", value):
                return InvalidFormat(key, value)
            elif key == 'x-trans-id' and \
                not re.match("^tx[0-9a-f]{21}-[0-9a-f]{10}.*", value):
                return InvalidFormat(key, value)
            elif key == 'accept-ranges' and not value == 'bytes':
                return InvalidFormat(key, value)
            elif key == 'etag' and not value.isalnum():
                return InvalidFormat(key, value)
            elif key == 'transfer-encoding' and not value == 'chunked':
                return InvalidFormat(key, value)

        return None


class InvalidFormat(object):
    """Informs an error message if a format of a certain header is invalid"""

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def describe(self):
        return "InvalidFormat (%s, %s)" % (self.key, self.value)

    def get_details(self):
        return {}


class MatchesDictExceptForKeys(object):
    """Matches two dictionaries.

    Verifies all items are equals except for those identified by a list of keys
    """

    def __init__(self, expected, excluded_keys=None):
        self.expected = expected
        self.excluded_keys = excluded_keys if excluded_keys is not None else []

    def match(self, actual):
        filtered_expected = helpers.dict_subtract(self.expected,
                                                  self.excluded_keys)
        filtered_actual = helpers.dict_subtract(actual,
                                                self.excluded_keys)
        if filtered_actual != filtered_expected:
            return DictMismatch(filtered_expected, filtered_actual)


class DictMismatch(object):
    """Mismatch between two dicts describes deltas"""

    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        self.intersect = set(self.expected) & set(self.actual)
        self.symmetric_diff = set(self.expected) ^ set(self.actual)

    def _format_dict(self, dict_to_format):
        # Ensure the error string dict is printed in a set order
        # NOTE(mtreinish): needed to ensure a deterministic error msg for
        # testing. Otherwise the error message will be dependent on the
        # dict ordering.
        dict_string = "{"
        for key in sorted(dict_to_format):
            dict_string += "'%s': %s, " % (key, dict_to_format[key])
        dict_string = dict_string[:-2] + '}'
        return dict_string

    def describe(self):
        msg = ""
        if self.symmetric_diff:
            only_expected = helpers.dict_subtract(self.expected, self.actual)
            only_actual = helpers.dict_subtract(self.actual, self.expected)
            if only_expected:
                msg += "Only in expected:\n  %s\n" % self._format_dict(
                    only_expected)
            if only_actual:
                msg += "Only in actual:\n  %s\n" % self._format_dict(
                    only_actual)
        diff_set = set(o for o in self.intersect if
                       self.expected[o] != self.actual[o])
        if diff_set:
            msg += "Differences:\n"
            for o in diff_set:
                msg += "  %s: expected %s, actual %s\n" % (
                    o, self.expected[o], self.actual[o])
        return msg

    def get_details(self):
        return {}
