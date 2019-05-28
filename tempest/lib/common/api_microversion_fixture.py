# Copyright 2019 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures

from tempest.lib.services.compute import base_compute_client
from tempest.lib.services.placement import base_placement_client
from tempest.lib.services.volume import base_client as base_volume_client


class APIMicroversionFixture(fixtures.Fixture):
    """API Microversion Fixture to set service microversion.

    This class provides the fixture to set and reset the microversion
    on service client. Service client has global variable to set the
    microversion for that service API request.
    For example: base_compute_client.COMPUTE_MICROVERSION
    Global variable is always risky to set directly which can affect the
    other test's API request also. This class provides a way to reset the
    service microversion once test finish the API request.
    This class can be used with useFixture: Example::

        def setUp(self):
            super(BaseV2ComputeTest, self).setUp()
            self.useFixture(api_microversion_fixture.APIMicroversionFixture(
                compute_microversion=self.compute_request_microversion))

    Or you can set microversion on multiple services together::

        def setUp(self):
            super(ScenarioTest, self).setUp()
            self.useFixture(api_microversion_fixture.APIMicroversionFixture(
                compute_microversion=self.compute_request_microversion,
                volume_microversion=self.volume_request_microversion))

    Current supported services:
    - Compute
    - Volume
    - Placement

    :param str compute_microversion: microvesion to be set on compute
                                     service clients
    :param str volume_microversion: microvesion to be set on volume
                                    service clients
    :param str placement_microversion: microvesion to be set on placement
                                       service clients
    """

    def __init__(self, compute_microversion=None, volume_microversion=None,
                 placement_microversion=None):
        self.compute_microversion = compute_microversion
        self.volume_microversion = volume_microversion
        self.placement_microversion = placement_microversion

    def _setUp(self):
        super(APIMicroversionFixture, self)._setUp()
        if self.compute_microversion:
            base_compute_client.COMPUTE_MICROVERSION = (
                self.compute_microversion)
        if self.volume_microversion:
            base_volume_client.VOLUME_MICROVERSION = self.volume_microversion
        if self.placement_microversion:
            base_placement_client.PLACEMENT_MICROVERSION = (
                self.placement_microversion)

        self.addCleanup(self._reset_microversion)

    def _reset_microversion(self):
        base_compute_client.COMPUTE_MICROVERSION = None
        base_volume_client.VOLUME_MICROVERSION = None
        base_placement_client.PLACEMENT_MICROVERSION = None
