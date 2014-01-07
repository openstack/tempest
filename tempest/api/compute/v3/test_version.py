# Copyright 2014 NEC Corporation.
# All Rights Reserved.
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


from tempest.api.compute import base
from tempest import test


class VersionV3TestJSON(base.BaseV3ComputeTest):
    _interface = 'json'

    @test.attr(type='gate')
    def test_version(self):
        # Get version information
        resp, version = self.version_client.get_version()
        self.assertEqual(200, resp.status)
        self.assertIn("id", version)
        self.assertEqual("v3.0", version["id"])


class VersionV3TestXML(VersionV3TestJSON):
    _interface = 'xml'
