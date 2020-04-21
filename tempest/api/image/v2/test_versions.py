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

from tempest.api.image import base
from tempest.lib import decorators


class VersionsTest(base.BaseV2ImageTest):
    """Test image versions"""

    @decorators.idempotent_id('659ea30a-a17c-4317-832c-0f68ed23c31d')
    @decorators.attr(type='smoke')
    def test_list_versions(self):
        """Test listing image versions"""
        versions = self.versions_client.list_versions()['versions']
        expected_resources = ('id', 'links', 'status')

        for version in versions:
            for res in expected_resources:
                self.assertIn(res, version)
