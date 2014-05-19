# Copyright 2013 Huawei Technologies Co.,LTD.
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

import uuid

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class HypervisorAdminNegativeV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests Hypervisors API that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(HypervisorAdminNegativeV3Test, cls).setUpClass()
        cls.client = cls.hypervisor_admin_client
        cls.non_adm_client = cls.hypervisor_client

    def _list_hypervisors(self):
        # List of hypervisors
        resp, hypers = self.client.get_hypervisor_list()
        self.assertEqual(200, resp.status)
        return hypers

    @test.attr(type=['negative', 'gate'])
    def test_show_nonexistent_hypervisor(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            exceptions.NotFound,
            self.client.get_hypervisor_show_details,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    def test_show_hypervisor_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_show_details,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    def test_show_servers_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_servers,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    def test_show_servers_with_nonexistent_hypervisor(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            exceptions.NotFound,
            self.client.get_hypervisor_servers,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    def test_get_hypervisor_stats_with_non_admin_user(self):
        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_stats)

    @test.attr(type=['negative', 'gate'])
    def test_get_nonexistent_hypervisor_uptime(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            exceptions.NotFound,
            self.client.get_hypervisor_uptime,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    def test_get_hypervisor_uptime_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_uptime,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    def test_get_hypervisor_list_with_non_admin_user(self):
        # List of hypervisor and available services with non admin user
        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_list)

    @test.attr(type=['negative', 'gate'])
    def test_get_hypervisor_list_details_with_non_admin_user(self):
        # List of hypervisor details and available services with non admin user
        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_hypervisor_list_details)

    @test.attr(type=['negative', 'gate'])
    def test_search_nonexistent_hypervisor(self):
        nonexistent_hypervisor_name = data_utils.rand_name('test_hypervisor')

        resp, hypers = self.client.search_hypervisor(
            nonexistent_hypervisor_name)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(hypers))

    @test.attr(type=['negative', 'gate'])
    def test_search_hypervisor_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.search_hypervisor,
            hypers[0]['hypervisor_hostname'])
