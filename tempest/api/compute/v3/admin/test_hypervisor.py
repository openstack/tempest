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
from tempest import test


class HypervisorAdminV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests Hypervisors API that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(HypervisorAdminV3Test, cls).setUpClass()
        cls.client = cls.hypervisor_admin_client

    def _list_hypervisors(self):
        # List of hypervisors
        resp, hypers = self.client.get_hypervisor_list()
        self.assertEqual(200, resp.status)
        return hypers

    @test.attr(type='gate')
    def test_get_hypervisor_list(self):
        # List of hypervisor and available hypervisors hostname
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

    @test.attr(type='gate')
    def test_get_hypervisor_list_details(self):
        # Display the details of the all hypervisor
        resp, hypers = self.client.get_hypervisor_list_details()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hypers) > 0)

    @test.attr(type='gate')
    def test_get_hypervisor_show_details(self):
        # Display the details of the specified hypervisor
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        resp, details = (self.client.
                         get_hypervisor_show_details(hypers[0]['id']))
        self.assertEqual(200, resp.status)
        self.assertTrue(len(details) > 0)
        self.assertEqual(details['hypervisor_hostname'],
                         hypers[0]['hypervisor_hostname'])

    @test.attr(type='gate')
    def test_get_hypervisor_show_servers(self):
        # Show instances about the specific hypervisors
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        hypervisor_id = hypers[0]['id']
        resp, hypervisors = self.client.get_hypervisor_servers(hypervisor_id)
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hypervisors) > 0)

    @test.attr(type='gate')
    def test_get_hypervisor_stats(self):
        # Verify the stats of the all hypervisor
        resp, stats = self.client.get_hypervisor_stats()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(stats) > 0)

    @test.attr(type='gate')
    def test_get_hypervisor_uptime(self):
        # Verify that GET shows the specified hypervisor uptime
        hypers = self._list_hypervisors()

        resp, uptime = self.client.get_hypervisor_uptime(hypers[0]['id'])
        self.assertEqual(200, resp.status)
        self.assertTrue(len(uptime) > 0)

    @test.attr(type='gate')
    def test_search_hypervisor(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)
        resp, hypers = self.client.search_hypervisor(
            hypers[0]['hypervisor_hostname'])
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hypers) > 0)
