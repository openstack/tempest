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

from tempest.common import api_version_request
from tempest import exceptions


class BaseMicroversionTest(object):
    """Mixin class for API microversion test class."""

    # NOTE: Basically, each microversion is small API change and we
    # can use the same tests for most microversions in most cases.
    # So it is nice to define the test class as possible to run
    # for all microversions. We need to define microversion range
    # (min_microversion, max_microversion) on each test class if necessary.
    min_microversion = None
    max_microversion = 'latest'


def check_skip_with_microversion(test_min_version, test_max_version,
                                 cfg_min_version, cfg_max_version):
    min_version = api_version_request.APIVersionRequest(test_min_version)
    max_version = api_version_request.APIVersionRequest(test_max_version)
    config_min_version = api_version_request.APIVersionRequest(cfg_min_version)
    config_max_version = api_version_request.APIVersionRequest(cfg_max_version)
    if ((min_version > max_version) or
       (config_min_version > config_max_version)):
        msg = ("Min version is greater than Max version. Test Class versions "
               "[%s - %s]. configration versions [%s - %s]."
               % (min_version.get_string(),
                  max_version.get_string(),
                  config_min_version.get_string(),
                  config_max_version.get_string()))
        raise exceptions.InvalidConfiguration(msg)

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
               "configration range[%s - %s]."
               % (min_version.get_string(),
                  max_version.get_string(),
                  config_min_version.get_string(),
                  config_max_version.get_string()))
        raise testtools.TestCase.skipException(msg)


def select_request_microversion(test_min_version, cfg_min_version):
    test_version = api_version_request.APIVersionRequest(test_min_version)
    cfg_version = api_version_request.APIVersionRequest(cfg_min_version)
    max_version = cfg_version if cfg_version >= test_version else test_version
    return max_version.get_string()
