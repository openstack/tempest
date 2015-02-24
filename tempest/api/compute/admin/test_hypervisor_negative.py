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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class HypervisorAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Hypervisors API that require admin privileges
    """

    @classmethod
    def setup_clients(cls):
        super(HypervisorAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.hypervisor_client
        cls.non_adm_client = cls.hypervisor_client

    def _list_hypervisors(self):
        # List of hypervisors
        hypers = self.client.get_hypervisor_list()
        return hypers

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('c136086a-0f67-4b2b-bc61-8482bd68989f')
    def test_show_nonexistent_hypervisor(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            lib_exc.NotFound,
            self.client.get_hypervisor_show_details,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('51e663d0-6b89-4817-a465-20aca0667d03')
    def test_show_hypervisor_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_show_details,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('2a0a3938-832e-4859-95bf-1c57c236b924')
    def test_show_servers_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_servers,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('02463d69-0ace-4d33-a4a8-93d7883a2bba')
    def test_show_servers_with_nonexistent_hypervisor(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            lib_exc.NotFound,
            self.client.get_hypervisor_servers,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e2b061bb-13f9-40d8-9d6e-d5bf17595849')
    def test_get_hypervisor_stats_with_non_admin_user(self):
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_stats)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f60aa680-9a3a-4c7d-90e1-fae3a4891303')
    def test_get_nonexistent_hypervisor_uptime(self):
        nonexistent_hypervisor_id = str(uuid.uuid4())

        self.assertRaises(
            lib_exc.NotFound,
            self.client.get_hypervisor_uptime,
            nonexistent_hypervisor_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6c3461f9-c04c-4e2a-bebb-71dc9cb47df2')
    def test_get_hypervisor_uptime_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_uptime,
            hypers[0]['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('51b3d536-9b14-409c-9bce-c6f7c794994e')
    def test_get_hypervisor_list_with_non_admin_user(self):
        # List of hypervisor and available services with non admin user
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_list)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('dc02db05-e801-4c5f-bc8e-d915290ab345')
    def test_get_hypervisor_list_details_with_non_admin_user(self):
        # List of hypervisor details and available services with non admin user
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.get_hypervisor_list_details)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('19a45cc1-1000-4055-b6d2-28e8b2ec4faa')
    def test_search_nonexistent_hypervisor(self):
        nonexistent_hypervisor_name = data_utils.rand_name('test_hypervisor')

        self.assertRaises(
            lib_exc.NotFound,
            self.client.search_hypervisor,
            nonexistent_hypervisor_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('5b6a6c79-5dc1-4fa5-9c58-9c8085948e74')
    def test_search_hypervisor_with_non_admin_user(self):
        hypers = self._list_hypervisors()
        self.assertTrue(len(hypers) > 0)

        self.assertRaises(
            lib_exc.Forbidden,
            self.non_adm_client.search_hypervisor,
            hypers[0]['hypervisor_hostname'])
