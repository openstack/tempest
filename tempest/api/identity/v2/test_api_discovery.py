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
from tempest.lib import decorators


class TestApiDiscovery(base.BaseIdentityV2Test):
    """Tests for identity v2 API discovery features."""

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('ea889a68-a15f-4166-bfb1-c12456eae853')
    def test_api_version_resources(self):
        """Test showing identity v2 api version resources"""
        descr = self.non_admin_client.show_api_description()['version']
        expected_resources = ('id', 'links', 'media-types', 'status',
                              'updated')

        keys = descr.keys()
        for res in expected_resources:
            self.assertIn(res, keys)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('007a0be0-78fe-4fdb-bbee-e9216cc17bb2')
    def test_api_media_types(self):
        """Test showing identity v2 api version media type"""
        descr = self.non_admin_client.show_api_description()['version']
        # Get MIME type bases and descriptions
        media_types = [(media_type['base'], media_type['type']) for
                       media_type in descr['media-types']]
        # These are supported for API version 2
        supported_types = [('application/json',
                            'application/vnd.openstack.identity-v2.0+json')]

        # Check if supported types exist in response body
        for s_type in supported_types:
            self.assertIn(s_type, media_types)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('77fd6be0-8801-48e6-b9bf-38cdd2f253ec')
    def test_api_version_statuses(self):
        """Test showing identity v2 api version status"""
        descr = self.non_admin_client.show_api_description()['version']
        status = descr['status'].lower()
        supported_statuses = ['current', 'stable', 'experimental',
                              'supported', 'deprecated']

        self.assertIn(status, supported_statuses)
