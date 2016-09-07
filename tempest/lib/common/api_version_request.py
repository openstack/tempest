# Copyright 2014 IBM Corp.
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

from tempest.lib import exceptions


# Define the minimum and maximum version of the API across all of the
# REST API. The format of the version is:
# X.Y where:
#
# - X will only be changed if a significant backwards incompatible API
# change is made which affects the API as whole. That is, something
# that is only very very rarely incremented.
#
# - Y when you make any change to the API. Note that this includes
# semantic changes which may not affect the input or output formats or
# even originate in the API code layer. We are not distinguishing
# between backwards compatible and backwards incompatible changes in
# the versioning system. It must be made clear in the documentation as
# to what is a backwards compatible change and what is a backwards
# incompatible one.

class APIVersionRequest(object):
    """This class represents an API Version Request.

    This class provides convenience methods for manipulation
    and comparison of version numbers that we need to do to
    implement microversions.

    :param version_string: String representation of APIVersionRequest.
            Correct format is 'X.Y', where 'X' and 'Y' are int values.
            None value should be used to create Null APIVersionRequest,
            which is equal to 0.0
    """

    # NOTE: This 'latest' version is a magic number, we assume any
    # projects(Nova, etc.) never achieve this number.
    latest_ver_major = 99999
    latest_ver_minor = 99999

    def __init__(self, version_string=None):
        """Create an API version request object."""
        # NOTE(gmann): 'version_string' as String "None" will be considered as
        # invalid version string.
        self.ver_major = 0
        self.ver_minor = 0

        if version_string is not None:
            match = re.match(r"^([1-9]\d*)\.([1-9]\d*|0)$",
                             version_string)
            if match:
                self.ver_major = int(match.group(1))
                self.ver_minor = int(match.group(2))
            elif version_string == 'latest':
                self.ver_major = self.latest_ver_major
                self.ver_minor = self.latest_ver_minor
            else:
                raise exceptions.InvalidAPIVersionString(
                    version=version_string)

    def __str__(self):
        """Debug/Logging representation of object."""
        return ("API Version Request: %s" % self.get_string())

    def is_null(self):
        """Checks whether version is null.

        Return True if version object is null otherwise False.

        :returns: boolean
        """
        return self.ver_major == 0 and self.ver_minor == 0

    def _format_type_error(self, other):
        return TypeError("'%(other)s' should be an instance of '%(cls)s'" %
                         {"other": other, "cls": self.__class__})

    def __lt__(self, other):
        if not isinstance(other, APIVersionRequest):
            raise self._format_type_error(other)

        return ((self.ver_major, self.ver_minor) <
                (other.ver_major, other.ver_minor))

    def __eq__(self, other):
        if not isinstance(other, APIVersionRequest):
            raise self._format_type_error(other)

        return ((self.ver_major, self.ver_minor) ==
                (other.ver_major, other.ver_minor))

    def __gt__(self, other):
        if not isinstance(other, APIVersionRequest):
            raise self._format_type_error(other)

        return ((self.ver_major, self.ver_minor) >
                (other.ver_major, other.ver_minor))

    def __le__(self, other):
        return self < other or self == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        return self > other or self == other

    def matches(self, min_version, max_version):
        """Matches the version object.

        Returns whether the version object represents a version
        greater than or equal to the minimum version and less than
        or equal to the maximum version.

        :param min_version: Minimum acceptable version.
        :param max_version: Maximum acceptable version.
        :returns: boolean

        If min_version is null then there is no minimum limit.
        If max_version is null then there is no maximum limit.
        If self is null then raise ValueError
        """

        if self.is_null():
            raise ValueError
        if max_version.is_null() and min_version.is_null():
            return True
        elif max_version.is_null():
            return min_version <= self
        elif min_version.is_null():
            return self <= max_version
        else:
            return min_version <= self <= max_version

    def get_string(self):
        """Version string representation.

        Converts object to string representation which if used to create
        an APIVersionRequest object results in the same version request.
        """
        if self.is_null():
            return None
        if (self.ver_major == self.latest_ver_major and
            self.ver_minor == self.latest_ver_minor):
            return 'latest'
        return "%s.%s" % (self.ver_major, self.ver_minor)
