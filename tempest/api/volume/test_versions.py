# Copyright 2017 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.volume import base
from tempest.lib import decorators


class VersionsTest(base.BaseVolumeTest):

    _api_version = 3

    @decorators.idempotent_id('77838fc4-b49b-4c64-9533-166762517369')
    @decorators.attr(type='smoke')
    def test_list_versions(self):
        # NOTE: The version data is checked on service client side
        #       with JSON-Schema validation. It is enough to just call
        #       the API here.
        self.versions_client.list_versions()
