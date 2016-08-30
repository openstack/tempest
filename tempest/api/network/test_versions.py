# Copyright 2016 VMware, Inc.
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

from tempest.api.network import base
from tempest import test


class NetworksApiDiscovery(base.BaseNetworkTest):
    @test.attr(type='smoke')
    @test.idempotent_id('cac8a836-c2e0-4304-b556-cd299c7281d1')
    def test_api_version_resources(self):
        """Test that GET / returns expected resources.

        The versions document returned by Neutron returns a few other
        resources other than just available API versions: it also
        states the status of each API version and provides links to
        schema.
        """

        result = self.network_versions_client.list_versions()
        expected_versions = ('v2.0')
        expected_resources = ('id', 'links', 'status')
        received_list = result.values()

        for item in received_list:
            for version in item:
                for resource in expected_resources:
                    self.assertIn(resource, version)
                self.assertIn(version['id'], expected_versions)
