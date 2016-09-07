# Copyright 2016 NEC Corporation.  All rights reserved.
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


class APIMicroversionFixture(fixtures.Fixture):

    def __init__(self, compute_microversion):
        self.compute_microversion = compute_microversion

    def _setUp(self):
        super(APIMicroversionFixture, self)._setUp()
        base_compute_client.COMPUTE_MICROVERSION = self.compute_microversion
        self.addCleanup(self._reset_compute_microversion)

    def _reset_compute_microversion(self):
        base_compute_client.COMPUTE_MICROVERSION = None
