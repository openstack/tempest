# Copyright 2015 OpenStack Foundation.
# Copyright 2015, Red Hat, Inc.
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

from tempest.api.identity import base
from tempest import test


class TestApiDiscovery(base.BaseIdentityV3Test):
    """Tests for API discovery features."""

    @test.attr(type='smoke')
    @test.idempotent_id('b9232f5e-d9e5-4d97-b96c-28d3db4de1bd')
    def test_api_version_resources(self):
        descr = self.non_admin_client.show_api_description()['version']
        expected_resources = ('id', 'links', 'media-types', 'status',
                              'updated')

        keys = descr.keys()
        for res in expected_resources:
            self.assertIn(res, keys)

    @test.attr(type='smoke')
    @test.idempotent_id('657c1970-4722-4189-8831-7325f3bc4265')
    def test_api_media_types(self):
        descr = self.non_admin_client.show_api_description()['version']
        # Get MIME type bases and descriptions
        media_types = [(media_type['base'], media_type['type']) for
                       media_type in descr['media-types']]
        # These are supported for API version 2
        supported_types = [('application/json',
                            'application/vnd.openstack.identity-v3+json')]

        # Check if supported types exist in response body
        for s_type in supported_types:
            self.assertIn(s_type, media_types)

    @test.attr(type='smoke')
    @test.idempotent_id('8879a470-abfb-47bb-bb8d-5a7fd279ad1e')
    def test_api_version_statuses(self):
        descr = self.non_admin_client.show_api_description()['version']
        status = descr['status'].lower()
        supported_statuses = ['current', 'stable', 'experimental',
                              'supported', 'deprecated']

        self.assertIn(status, supported_statuses)
