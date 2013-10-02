# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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
from tempest.common.utils.data_utils import rand_int_id
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class ServersAdminTestJSON(base.BaseComputeAdminTest):

    """
    Tests Servers API using admin privileges
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServersAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.servers_client
        cls.flavors_client = cls.os_adm.flavors_client

        cls.admin_client = cls._get_identity_admin_client()
        tenant = cls.admin_client.get_tenant_by_name(
            cls.client.tenant_name)
        cls.tenant_id = tenant['id']

        cls.s1_name = rand_name('server')
        resp, server = cls.create_server(name=cls.s1_name,
                                         wait_until='ACTIVE')
        cls.s1_id = server['id']

        cls.s2_name = rand_name('server')
        resp, server = cls.create_server(name=cls.s2_name,
                                         wait_until='ACTIVE')

    def _get_unused_flavor_id(self):
        flavor_id = rand_int_id(start=1000)
        while True:
            try:
                resp, body = self.flavors_client.get_flavor_details(flavor_id)
            except exceptions.NotFound:
                break
            flavor_id = rand_int_id(start=1000)
        return flavor_id

    @attr(type='gate')
    def test_list_servers_by_admin(self):
        # Listing servers by admin user returns empty list by default
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']
        self.assertEqual('200', resp['status'])
        self.assertEqual([], servers)

    @attr(type='gate')
    def test_list_servers_by_admin_with_all_tenants(self):
        # Listing servers by admin user with all tenants parameter
        # Here should be listed all servers
        params = {'all_tenants': ''}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        servers_name = map(lambda x: x['name'], servers)

        self.assertIn(self.s1_name, servers_name)
        self.assertIn(self.s2_name, servers_name)

    @attr(type='gate')
    def test_admin_delete_servers_of_others(self):
        # Administrator can delete servers of others
        _, server = self.create_server()
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])
        self.servers_client.wait_for_server_termination(server['id'])

    @attr(type=['negative', 'gate'])
    def test_resize_server_using_overlimit_ram(self):
        flavor_name = rand_name("flavor-")
        flavor_id = self._get_unused_flavor_id()
        resp, quota_set = self.quotas_client.get_default_quota_set(
            self.tenant_id)
        ram = int(quota_set['ram']) + 1
        vcpus = 8
        disk = 10
        resp, flavor_ref = self.flavors_client.create_flavor(flavor_name,
                                                             ram, vcpus, disk,
                                                             flavor_id)
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises(exceptions.OverLimit,
                          self.client.resize,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @attr(type=['negative', 'gate'])
    def test_resize_server_using_overlimit_vcpus(self):
        flavor_name = rand_name("flavor-")
        flavor_id = self._get_unused_flavor_id()
        ram = 512
        resp, quota_set = self.quotas_client.get_default_quota_set(
            self.tenant_id)
        vcpus = int(quota_set['cores']) + 1
        disk = 10
        resp, flavor_ref = self.flavors_client.create_flavor(flavor_name,
                                                             ram, vcpus, disk,
                                                             flavor_id)
        self.addCleanup(self.flavors_client.delete_flavor, flavor_id)
        self.assertRaises(exceptions.OverLimit,
                          self.client.resize,
                          self.servers[0]['id'],
                          flavor_ref['id'])

    @attr(type='gate')
    def test_reset_state_server(self):
        # Reset server's state to 'error'
        resp, server = self.client.reset_state(self.s1_id)
        self.assertEqual(202, resp.status)

        # Verify server's state
        resp, server = self.client.get_server(self.s1_id)
        self.assertEqual(server['status'], 'ERROR')

        # Reset server's state to 'active'
        resp, server = self.client.reset_state(self.s1_id, state='active')
        self.assertEqual(202, resp.status)

        # Verify server's state
        resp, server = self.client.get_server(self.s1_id)
        self.assertEqual(server['status'], 'ACTIVE')

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_invalid_state(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state='invalid')

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_invalid_type(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.reset_state, self.s1_id,
                          state=1)

    @attr(type=['negative', 'gate'])
    def test_reset_state_server_nonexistent_server(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.reset_state, '999')


class ServersAdminTestXML(ServersAdminTestJSON):
    _interface = 'xml'
