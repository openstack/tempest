# Copyright 2016 OpenStack Foundation
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

import operator

from tempest.api.volume import base
from tempest.lib import decorators


class BackendsCapabilitiesAdminTestsJSON(base.BaseVolumeAdminTest):
    """Test backends capabilities"""

    @classmethod
    def resource_setup(cls):
        super(BackendsCapabilitiesAdminTestsJSON, cls).resource_setup()
        # Get host list, formation: host@backend-name
        cls.hosts = [
            pool['name'] for pool in
            cls.admin_scheduler_stats_client.list_pools()['pools']
        ]

    @decorators.idempotent_id('3750af44-5ea2-4cd4-bc3e-56e7e6caf854')
    def test_get_capabilities_backend(self):
        """Test getting backend capabilities"""
        # Check response schema
        self.admin_capabilities_client.show_backend_capabilities(self.hosts[0])

    @decorators.idempotent_id('a9035743-d46a-47c5-9cb7-3c80ea16dea0')
    def test_compare_volume_stats_values(self):
        """Test comparing volume stats values

        Compare volume stats between show_backend_capabilities and show_pools.
        """
        VOLUME_STATS = ('vendor_name',
                        'volume_backend_name',
                        'storage_protocol')

        # Get list backend capabilities using show_pools
        cinder_pools = [
            pool['capabilities'] for pool in
            self.admin_scheduler_stats_client.list_pools(detail=True)['pools']
        ]

        # Get list backends capabilities using show_backend_capabilities
        capabilities = [
            self.admin_capabilities_client.show_backend_capabilities(
                host=host) for host in self.hosts
        ]

        # Returns a tuple of VOLUME_STATS values
        expected_list = sorted(list(map(operator.itemgetter(*VOLUME_STATS),
                                        cinder_pools)))
        observed_list = sorted(list(map(operator.itemgetter(*VOLUME_STATS),
                                        capabilities)))
        self.assertEqual(expected_list, observed_list)
