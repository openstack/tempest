# Copyright 2013 Huawei Technologies Co.,LTD.
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class HostsAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests hosts API using admin privileges.
    """

    @classmethod
    def setup_clients(cls):
        super(HostsAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.hosts_client
        cls.non_admin_client = cls.os.hosts_client

    def _get_host_name(self):
        hosts = self.client.list_hosts()
        self.assertTrue(len(hosts) >= 1)
        hostname = hosts[0]['host_name']
        return hostname

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('dd032027-0210-4d9c-860e-69b1b8deed5f')
    def test_list_hosts_with_non_admin_user(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.list_hosts)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e75b0a1a-041f-47a1-8b4a-b72a6ff36d3f')
    def test_show_host_detail_with_nonexistent_hostname(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_host_detail, nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('19ebe09c-bfd4-4b7c-81a2-e2e0710f59cc')
    def test_show_host_detail_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.show_host_detail,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e40c72b1-0239-4ed6-ba21-81a184df1f7c')
    def test_update_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('76e396fe-5418-4dd3-a186-5b301edc0721')
    def test_update_host_with_extra_param(self):
        # only 'status' and 'maintenance_mode' are the valid params.
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='enable',
                          param='XXX')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('fbe2bf3e-3246-4a95-a59f-94e4e298ec77')
    def test_update_host_with_invalid_status(self):
        # 'status' can only be 'enable' or 'disable'
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='invalid',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ab1e230e-5e22-41a9-8699-82b9947915d4')
    def test_update_host_with_invalid_maintenance_mode(self):
        # 'maintenance_mode' can only be 'enable' or 'disable'
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='invalid')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0cd85f75-6992-4a4a-b1bd-d11e37fd0eee')
    def test_update_host_without_param(self):
        # 'status' or 'maintenance_mode' needed for host update
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('23c92146-2100-4d68-b2d6-c7ade970c9c1')
    def test_update_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(lib_exc.NotFound,
                          self.client.update_host,
                          nonexitent_hostname,
                          status='enable',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0d981ac3-4320-4898-b674-82b61fbb60e4')
    def test_startup_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(lib_exc.NotFound,
                          self.client.startup_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9f4ebb7e-b2ae-4e5b-a38f-0fd1bb0ddfca')
    def test_startup_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.startup_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('9e637444-29cf-4244-88c8-831ae82c31b6')
    def test_shutdown_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(lib_exc.NotFound,
                          self.client.shutdown_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a803529c-7e3f-4d3c-a7d6-8e1c203d27f6')
    def test_shutdown_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.shutdown_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f86bfd7b-0b13-4849-ae29-0322e83ee58b')
    def test_reboot_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(lib_exc.NotFound,
                          self.client.reboot_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('02d79bb9-eb57-4612-abf6-2cb38897d2f8')
    def test_reboot_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reboot_host,
                          hostname)
