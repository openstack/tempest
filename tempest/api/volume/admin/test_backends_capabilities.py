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

    @staticmethod
    def _change_capabilities_storage_protocol(capabilities):
        """Convert storage_protocol to its canonical version"""
        # List of storage protocols variants defined in cinder.common.constants
        # The canonical name for storage protocol comes first in the list
        VARIANTS = [['iSCSI', 'iscsi'], ['FC', 'fibre_channel', 'fc'],
                    ['NFS', 'nfs'], ['NVMe-oF', 'NVMeOF', 'nvmeof']]

        capabilities = sorted(list(capabilities))

        # Cinder Bug #1966103: Some drivers were reporting different strings
        # to represent the same storage protocol. For backward compatibility,
        # the scheduler can handle the variants, but to standardize this for
        # operators (who may need to refer to the protocol in volume-type
        # extra-specs), the get-pools and get-capabilities response was changed
        # to only report the canonical name for a storage protocol, but these
        # 2 REST API call swere not changed simultaneously, so we may or may
        # not get canonical names, so just convert canonical names.
        for item in range(len(capabilities)):
            for variants in VARIANTS:
                if capabilities[item][2] in variants:
                    capabilities[item] = (capabilities[item][0],
                                          capabilities[item][1],
                                          variants[0])

        return capabilities

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
        expected_list = self._change_capabilities_storage_protocol(
            map(operator.itemgetter(*VOLUME_STATS), cinder_pools))
        observed_list = self._change_capabilities_storage_protocol(
            map(operator.itemgetter(*VOLUME_STATS), capabilities))

        self.assertEqual(expected_list, observed_list)
