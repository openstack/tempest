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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class HostsAdminNegativeV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests hosts API using admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(HostsAdminNegativeV3Test, cls).setUpClass()
        cls.client = cls.hosts_admin_client
        cls.non_admin_client = cls.hosts_client

    def _get_host_name(self):
        resp, hosts = self.client.list_hosts()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hosts) >= 1)
        hostname = hosts[0]['host_name']
        return hostname

    @test.attr(type=['negative', 'gate'])
    def test_list_hosts_with_non_admin_user(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_hosts)

    @test.attr(type=['negative', 'gate'])
    def test_show_host_detail_with_nonexistent_hostname(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')
        self.assertRaises(exceptions.NotFound,
                          self.client.show_host_detail, nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    def test_show_host_detail_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.show_host_detail,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    def test_update_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    def test_update_host_with_extra_param(self):
        # only 'status' and 'maintenance_mode' are the valid params.
        hostname = self._get_host_name()

        self.assertRaises(exceptions.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='enable',
                          param='XXX')

    @test.attr(type=['negative', 'gate'])
    def test_update_host_with_invalid_status(self):
        # 'status' can only be 'enable' or 'disable'
        hostname = self._get_host_name()

        self.assertRaises(exceptions.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='invalid',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    def test_update_host_with_invalid_maintenance_mode(self):
        # 'maintenance_mode' can only be 'enable' or 'disable'
        hostname = self._get_host_name()

        self.assertRaises(exceptions.BadRequest,
                          self.client.update_host,
                          hostname,
                          status='enable',
                          maintenance_mode='invalid')

    @test.attr(type=['negative', 'gate'])
    def test_update_host_without_param(self):
        # 'status' or 'maintenance_mode' needed for host update
        hostname = self._get_host_name()

        self.assertRaises(exceptions.BadRequest,
                          self.client.update_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    def test_update_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(exceptions.NotFound,
                          self.client.update_host,
                          nonexitent_hostname,
                          status='enable',
                          maintenance_mode='enable')

    @test.attr(type=['negative', 'gate'])
    def test_startup_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(exceptions.NotFound,
                          self.client.startup_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    def test_startup_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.startup_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    def test_shutdown_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(exceptions.NotFound,
                          self.client.shutdown_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    def test_shutdown_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.shutdown_host,
                          hostname)

    @test.attr(type=['negative', 'gate'])
    def test_reboot_nonexistent_host(self):
        nonexitent_hostname = data_utils.rand_name('rand_hostname')

        self.assertRaises(exceptions.NotFound,
                          self.client.reboot_host,
                          nonexitent_hostname)

    @test.attr(type=['negative', 'gate'])
    def test_reboot_host_with_non_admin_user(self):
        hostname = self._get_host_name()

        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.reboot_host,
                          hostname)
