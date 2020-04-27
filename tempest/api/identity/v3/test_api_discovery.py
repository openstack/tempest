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
from tempest import config
from tempest.lib import decorators


CONF = config.CONF


class TestApiDiscovery(base.BaseIdentityV3Test):
    """Tests for identity API discovery features."""

    @decorators.idempotent_id('79aec9ae-710f-4c54-a4fc-3aa25b4feac3')
    def test_identity_v3_existence(self):
        """Test that identity v3 version should exist"""
        versions = self.non_admin_versions_client.list_versions()
        found = any(
            "v3" in version.get('id')
            for version in versions['versions']['values'])
        self.assertEqual(CONF.identity_feature_enabled.api_v3, found)

    @decorators.idempotent_id('721f480f-35b6-46c7-846e-047e6acea0dc')
    @decorators.attr(type='smoke')
    def test_list_api_versions(self):
        """Test listing identity api versions

        NOTE: Actually this API doesn't depend on v3 API at all, because
        the API operation is "GET /" without v3's endpoint. The reason of
        this test path is just v3 API is CURRENT on Keystone side.
        """
        versions = self.non_admin_versions_client.list_versions()
        expected_resources = ('id', 'links', 'media-types', 'status',
                              'updated')

        for version in versions['versions']["values"]:
            for res in expected_resources:
                self.assertIn(res, version)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('b9232f5e-d9e5-4d97-b96c-28d3db4de1bd')
    def test_api_version_resources(self):
        """Test showing identity v3 api version resources"""
        descr = self.non_admin_client.show_api_description()['version']
        expected_resources = ('id', 'links', 'media-types', 'status',
                              'updated')

        keys = descr.keys()
        for res in expected_resources:
            self.assertIn(res, keys)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('657c1970-4722-4189-8831-7325f3bc4265')
    def test_api_media_types(self):
        """Test showing identity v3 api version media type"""
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

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('8879a470-abfb-47bb-bb8d-5a7fd279ad1e')
    def test_api_version_statuses(self):
        """Test showing identity v3 api version status"""
        descr = self.non_admin_client.show_api_description()['version']
        status = descr['status'].lower()
        supported_statuses = ['current', 'stable', 'experimental',
                              'supported', 'deprecated']

        self.assertIn(status, supported_statuses)
