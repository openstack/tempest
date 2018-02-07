# Copyright 2013 IBM Corporation
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
from tempest.lib import decorators


class HypervisorAdminTestBase(base.BaseV2ComputeAdminTest):
    """Tests Hypervisors API that require admin privileges"""

    @classmethod
    def setup_clients(cls):
        super(HypervisorAdminTestBase, cls).setup_clients()
        cls.client = cls.os_admin.hypervisor_client

    def _list_hypervisors(self):
        # List of hypervisors
        hypers = self.client.list_hypervisors()['hypervisors']
        return hypers


class HypervisorAdminTestJSON(HypervisorAdminTestBase):
    """Tests Hypervisors API that require admin privileges"""

    @decorators.idempotent_id('7f0ceacd-c64d-4e96-b8ee-d02943142cc5')
    def test_get_hypervisor_list(self):
        # List of hypervisor and available hypervisors hostname
        hypers = self._list_hypervisors()
        self.assertNotEmpty(hypers, "No hypervisors found.")

    @decorators.idempotent_id('1e7fdac2-b672-4ad1-97a4-bad0e3030118')
    def test_get_hypervisor_list_details(self):
        # Display the details of the all hypervisor
        hypers = self.client.list_hypervisors(detail=True)['hypervisors']
        self.assertNotEmpty(hypers, "No hypervisors found.")

    @decorators.idempotent_id('94ff9eae-a183-428e-9cdb-79fde71211cc')
    def test_get_hypervisor_show_details(self):
        # Display the details of the specified hypervisor
        hypers = self._list_hypervisors()
        self.assertNotEmpty(hypers, "No hypervisors found.")

        details = self.client.show_hypervisor(hypers[0]['id'])['hypervisor']
        self.assertNotEmpty(details)
        self.assertEqual(details['hypervisor_hostname'],
                         hypers[0]['hypervisor_hostname'])

    @decorators.idempotent_id('797e4f28-b6e0-454d-a548-80cc77c00816')
    def test_get_hypervisor_stats(self):
        # Verify the stats of the all hypervisor
        stats = (self.client.show_hypervisor_statistics()
                 ['hypervisor_statistics'])
        self.assertNotEmpty(stats)

    @decorators.idempotent_id('91a50d7d-1c2b-4f24-b55a-a1fe20efca70')
    def test_get_hypervisor_uptime(self):
        # Verify that GET shows the specified hypervisor uptime
        hypers = self._list_hypervisors()

        # Ironic will register each baremetal node as a 'hypervisor',
        # so the hypervisor list can contain many hypervisors of type
        # 'ironic'. If they are ALL ironic, skip this test since ironic
        # doesn't support hypervisor uptime. Otherwise, remove them
        # from the list of hypervisors to test.
        ironic_only = True
        hypers_without_ironic = []
        for hyper in hypers:
            details = (self.client.show_hypervisor(hyper['id'])
                       ['hypervisor'])
            if details['hypervisor_type'] != 'ironic':
                hypers_without_ironic.append(hyper)
                ironic_only = False

        if ironic_only:
            raise self.skipException(
                "Ironic does not support hypervisor uptime")

        has_valid_uptime = False
        for hyper in hypers_without_ironic:
            # because hypervisors might be disabled, this loops looking
            # for any good hit.
            try:
                uptime = (self.client.show_hypervisor_uptime(hyper['id'])
                          ['hypervisor'])
                if uptime:
                    has_valid_uptime = True
                    break
            except Exception:
                pass
        self.assertTrue(
            has_valid_uptime,
            "None of the hypervisors had a valid uptime: %s" % hypers)


class HypervisorAdminUnderV252Test(HypervisorAdminTestBase):
    max_microversion = '2.52'

    @decorators.idempotent_id('e81bba3f-6215-4e39-a286-d52d2f906862')
    def test_get_hypervisor_show_servers(self):
        # Show instances about the specific hypervisors
        hypers = self._list_hypervisors()
        self.assertNotEmpty(hypers, "No hypervisors found.")

        hostname = hypers[0]['hypervisor_hostname']
        hypervisors = (self.client.list_servers_on_hypervisor(hostname)
                       ['hypervisors'])
        self.assertNotEmpty(hypervisors)

    @decorators.idempotent_id('d7e1805b-3b14-4a3b-b6fd-50ec6d9f361f')
    def test_search_hypervisor(self):
        hypers = self._list_hypervisors()
        self.assertNotEmpty(hypers, "No hypervisors found.")
        hypers = self.client.search_hypervisor(
            hypers[0]['hypervisor_hostname'])['hypervisors']
        self.assertNotEmpty(hypers, "No hypervisors found.")
