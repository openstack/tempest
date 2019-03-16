# Copyright 2015 NEC Corporation.  All rights reserved.
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

import testtools

from tempest.lib.common import api_version_request
from tempest.lib import exceptions


LATEST_MICROVERSION = 'latest'


class BaseMicroversionTest(object):
    """Mixin class for API microversion test class."""

    # NOTE: Basically, each microversion is small API change and we
    # can use the same tests for most microversions in most cases.
    # So it is nice to define the test class as possible to run
    # for all microversions. We need to define microversion range
    # (min_microversion, max_microversion) on each test class if necessary.
    min_microversion = None
    max_microversion = LATEST_MICROVERSION


def check_skip_with_microversion(test_min_version, test_max_version,
                                 cfg_min_version, cfg_max_version):
    """Checks API microversions range and returns whether test needs to be skip

    Compare the test and configured microversion range and returns
    whether test microversion range is out of configured one.
    This method can be used to skip the test based on configured and test
    microversion range.

    :param test_min_version: Test Minimum Microversion
    :param test_max_version: Test Maximum Microversion
    :param cfg_min_version: Configured Minimum Microversion
    :param cfg_max_version: Configured Maximum Microversion
    :returns: boolean
    """

    min_version = api_version_request.APIVersionRequest(test_min_version)
    max_version = api_version_request.APIVersionRequest(test_max_version)
    config_min_version = api_version_request.APIVersionRequest(cfg_min_version)
    config_max_version = api_version_request.APIVersionRequest(cfg_max_version)
    if ((min_version > max_version) or
        (config_min_version > config_max_version)):
        msg = ("Test Class versions [%s - %s]. "
               "Configuration versions [%s - %s]."
               % (min_version.get_string(),
                  max_version.get_string(),
                  config_min_version.get_string(),
                  config_max_version.get_string()))
        raise exceptions.InvalidAPIVersionRange(msg)

    # NOTE: Select tests which are in range of configuration like
    #               config min           config max
    # ----------------+--------------------------+----------------
    # ...don't-select|
    #            ...select...  ...select...  ...select...
    #                                             |don't-select...
    # ......................select............................
    if (max_version < config_min_version or
        config_max_version < min_version):
        msg = ("The microversion range[%s - %s] of this test is out of the "
               "configuration range[%s - %s]."
               % (min_version.get_string(),
                  max_version.get_string(),
                  config_min_version.get_string(),
                  config_max_version.get_string()))
        raise testtools.TestCase.skipException(msg)


def select_request_microversion(test_min_version, cfg_min_version):
    """Select microversion from test and configuration min version.

    Compare requested microversion and return the maximum
    microversion out of those.

    :param test_min_version: Test Minimum Microversion
    :param cfg_min_version: Configured Minimum Microversion
    :returns: Selected microversion string
    """

    test_version = api_version_request.APIVersionRequest(test_min_version)
    cfg_version = api_version_request.APIVersionRequest(cfg_min_version)
    max_version = cfg_version if cfg_version >= test_version else test_version
    return max_version.get_string()


def assert_version_header_matches_request(api_microversion_header_name,
                                          api_microversion,
                                          response_header):
    """Checks API microversion in response header

    Verify whether microversion is present in response header
    and with specified 'api_microversion' value.

    :param api_microversion_header_name: Microversion header name
            Example- "X-OpenStack-Nova-API-Version"
    :param api_microversion: Microversion number like "2.10"
    :param response_header: Response header where microversion is
            expected to be present.
    """
    api_microversion_header_name = api_microversion_header_name.lower()
    if (api_microversion_header_name not in response_header or
        api_microversion != response_header[api_microversion_header_name]):
        msg = ("Microversion header '%s' with value '%s' does not match in "
               "response - %s. " % (api_microversion_header_name,
                                    api_microversion,
                                    response_header))
        raise exceptions.InvalidHTTPResponseHeader(msg)


def compare_version_header_to_response(api_microversion_header_name,
                                       api_microversion,
                                       response_header,
                                       operation='eq'):
    """Compares API microversion in response header to ``api_microversion``.

    Compare the ``api_microversion`` value in response header if microversion
    header is present in response, otherwise return false.

    To make this function work for APIs which do not return microversion
    header in response (example compute v2.0), this function does *not* raise
    InvalidHTTPResponseHeader.

    :param api_microversion_header_name: Microversion header name. Example:
        'Openstack-Api-Version'.
    :param api_microversion: Microversion number. Example:

        * '2.10' for the old-style header name, 'X-OpenStack-Nova-API-Version'
        * 'Compute 2.10' for the new-style header name, 'Openstack-Api-Version'

    :param response_header: Response header where microversion is
        expected to be present.
    :param operation: The boolean operation to use to compare the
        ``api_microversion`` to the microversion in ``response_header``.
        Can be 'lt', 'eq', 'gt', 'le', 'ne', 'ge'. Default is 'eq'. The
        operation type should be based on the order of the arguments:
        ``api_microversion`` <operation> ``response_header`` microversion.
    :returns: True if the comparison is logically true, else False if the
        comparison is logically false or if ``api_microversion_header_name`` is
        missing in the ``response_header``.
    :raises InvalidParam: If the operation is not lt, eq, gt, le, ne or ge.
    """
    api_microversion_header_name = api_microversion_header_name.lower()
    if api_microversion_header_name not in response_header:
        return False

    op = getattr(api_version_request.APIVersionRequest,
                 '__%s__' % operation, None)

    if op is None:
        msg = ("Operation %s is invalid. Valid options include: lt, eq, gt, "
               "le, ne, ge." % operation)
        raise exceptions.InvalidParam(invalid_param=msg)

    # Remove "volume" from "volume <microversion>", for example, so that the
    # microversion can be converted to `APIVersionRequest`.
    api_version = api_microversion.split(' ')[-1]
    resp_version = response_header[api_microversion_header_name].split(' ')[-1]
    if not op(
        api_version_request.APIVersionRequest(api_version),
        api_version_request.APIVersionRequest(resp_version)):
        return False

    return True
