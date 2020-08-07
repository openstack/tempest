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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class HostsAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    """Tests hosts API using admin privileges."""

    max_microversion = '2.42'

    @classmethod
    def setup_clients(cls):
        super(HostsAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os_admin.hosts_client
        cls.non_admin_client = cls.os_primary.hosts_client

    @classmethod
    def resource_setup(cls):
        super(HostsAdminNegativeTestJSON, cls).resource_setup()
        hosts = cls.client.list_hosts()['hosts']
        if not hosts:
            raise lib_exc.NotFound("no host found")
        cls.hostname = hosts[0]['host_name']

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('dd032027-0210-4d9c-860e-69b1b8deed5f')
    def test_list_hosts_with_non_admin_user(self):
        """Non admin user is not allowed to list hosts"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.list_hosts)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e75b0a1a-041f-47a1-8b4a-b72a6ff36d3f')
    def test_show_host_detail_with_nonexistent_hostname(self):
        """Showing host detail with not existing hostname should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_host, 'nonexistent_hostname')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('19ebe09c-bfd4-4b7c-81a2-e2e0710f59cc')
    def test_show_host_detail_with_non_admin_user(self):
        """Non admin user is not allowed to show host details"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.show_host,
                          self.hostname)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e40c72b1-0239-4ed6-ba21-81a184df1f7c')
    def test_update_host_with_non_admin_user(self):
        """Non admin user is not allowed to update host"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.update_host,
                          self.hostname,
                          status='enable',
                          maintenance_mode='enable')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fbe2bf3e-3246-4a95-a59f-94e4e298ec77')
    def test_update_host_with_invalid_status(self):
        """Updating host to invalid status should fail

        'status' can only be 'enable' or 'disable'.
        """
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          self.hostname,
                          status='invalid',
                          maintenance_mode='enable')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ab1e230e-5e22-41a9-8699-82b9947915d4')
    def test_update_host_with_invalid_maintenance_mode(self):
        """Updating host to invalid maintenance mode should fail

        'maintenance_mode' can only be 'enable' or 'disable'.
        """
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          self.hostname,
                          status='enable',
                          maintenance_mode='invalid')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0cd85f75-6992-4a4a-b1bd-d11e37fd0eee')
    def test_update_host_without_param(self):
        """Updating host without param should fail

        'status' or 'maintenance_mode' is needed for host update
        """
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_host,
                          self.hostname)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('23c92146-2100-4d68-b2d6-c7ade970c9c1')
    def test_update_nonexistent_host(self):
        """Updating not existing host should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_host,
                          'nonexistent_hostname',
                          status='enable',
                          maintenance_mode='enable')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0d981ac3-4320-4898-b674-82b61fbb60e4')
    def test_startup_nonexistent_host(self):
        """Starting up not existing host should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.startup_host,
                          'nonexistent_hostname')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9f4ebb7e-b2ae-4e5b-a38f-0fd1bb0ddfca')
    def test_startup_host_with_non_admin_user(self):
        """Non admin user is not allowed to startup host"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.startup_host,
                          self.hostname)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9e637444-29cf-4244-88c8-831ae82c31b6')
    def test_shutdown_nonexistent_host(self):
        """Shutting down not existing host should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.shutdown_host,
                          'nonexistent_hostname')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a803529c-7e3f-4d3c-a7d6-8e1c203d27f6')
    def test_shutdown_host_with_non_admin_user(self):
        """Non admin user is not allowed to shutdown host"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.shutdown_host,
                          self.hostname)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f86bfd7b-0b13-4849-ae29-0322e83ee58b')
    def test_reboot_nonexistent_host(self):
        """Rebooting not existing host should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.reboot_host,
                          'nonexistent_hostname')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('02d79bb9-eb57-4612-abf6-2cb38897d2f8')
    def test_reboot_host_with_non_admin_user(self):
        """Non admin user is not allowed to reboot host"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.reboot_host,
                          self.hostname)
