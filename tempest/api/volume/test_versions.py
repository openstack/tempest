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
    """Test volume versions"""

    _api_version = 3

    @decorators.idempotent_id('77838fc4-b49b-4c64-9533-166762517369')
    @decorators.attr(type='smoke')
    def test_list_versions(self):
        """Test listing volume versions"""
        # NOTE: The version data is checked on service client side
        #       with JSON-Schema validation. It is enough to just call
        #       the API here.
        self.versions_client.list_versions()

    @decorators.idempotent_id('7f755ae2-caa9-4049-988c-331d8f7a579f')
    def test_show_version(self):
        """Test getting volume version details"""
        # NOTE: The version data is checked on service client side
        # with JSON-Schema validation. So we will loop through each
        # version and call show version.
        versions = self.versions_client.list_versions()['versions']
        for version_dict in versions:
            version = version_dict['id']
            major_version = version.split('.')[0]
            response = self.versions_client.show_version(major_version)
            self.assertEqual(version, response['versions'][0]['id'])
