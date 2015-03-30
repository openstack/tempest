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

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators

from tempest.api.compute import base
from tempest.common import fixed_network
from tempest import test


class ServersAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Servers API using admin privileges
    """

    _host_key = 'OS-EXT-SRV-ATTR:host'

    @classmethod
    def setup_clients(cls):
        super(ServersAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.servers_client
        cls.non_admin_client = cls.servers_client
        cls.flavors_client = cls.os_adm.flavors_client

    @classmethod
    def resource_setup(cls):
        super(ServersAdminTestJSON, cls).resource_setup()

        cls.s1_name = data_utils.rand_name('server')
        server = cls.create_test_server(name=cls.s1_name,
                                        wait_until='ACTIVE')
        cls.s1_id = server['id']

        cls.s2_name = data_utils.rand_name('server')
        server = cls.create_test_server(name=cls.s2_name,
                                        wait_until='ACTIVE')
        cls.s2_id = server['id']

    @test.attr(type='gate')
    @test.idempotent_id('51717b38-bdc1-458b-b636-1cf82d99f62f')
    def test_list_servers_by_admin(self):
        # Listing servers by admin user returns empty list by default
        body = self.client.list_servers_with_detail()
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type='gate')
    @test.idempotent_id('06f960bb-15bb-48dc-873d-f96e89be7870')
    def test_list_servers_filter_by_error_status(self):
        # Filter the list of servers by server error status
        params = {'status': 'error'}
        self.client.reset_state(self.s1_id, state='error')
        body = self.non_admin_client.list_servers(params)
        # Reset server's state to 'active'
        self.client.reset_state(self.s1_id, state='active')
        # Verify server's state
        server = self.client.get_server(self.s1_id)
        self.assertEqual(server['status'], 'ACTIVE')
        servers = body['servers']
        # Verify error server in list result
        self.assertIn(self.s1_id, map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2_id, map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    @test.idempotent_id('9f5579ae-19b4-4985-a091-2a5d56106580')
    def test_list_servers_by_admin_with_all_tenants(self):
        # Listing servers by admin user with all tenants parameter
        # Here should be listed all servers
        params = {'all_tenants': ''}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        servers_name = map(lambda x: x['name'], servers)

        self.assertIn(self.s1_name, servers_name)
        self.assertIn(self.s2_name, servers_name)

    @test.attr(type='gate')
    @test.idempotent_id('7e5d6b8f-454a-4ba1-8ae2-da857af8338b')
    def test_list_servers_by_admin_with_specified_tenant(self):
        # In nova v2, tenant_id is ignored unless all_tenants is specified

        # List the primary tenant but get nothing due to odd specified behavior
        tenant_id = self.non_admin_client.tenant_id
        params = {'tenant_id': tenant_id}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        self.assertEqual([], servers)

        # List the admin tenant which has no servers
        admin_tenant_id = self.client.tenant_id
        params = {'all_tenants': '', 'tenant_id': admin_tenant_id}
        body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        self.assertEqual([], servers)

    @test.attr(type='gate')
    @test.idempotent_id('86c7a8f7-50cf-43a9-9bac-5b985317134f')
    def test_list_servers_filter_by_exist_host(self):
        # Filter the list of servers by existent host
        name = data_utils.rand_name('server')
        flavor = self.flavor_ref
        image_id = self.image_ref
        network = self.get_tenant_network()
        network_kwargs = fixed_network.set_networks_kwarg(network)
        test_server = self.client.create_server(name, image_id, flavor,
                                                **network_kwargs)
        self.addCleanup(self.client.delete_server, test_server['id'])
        self.client.wait_for_server_status(test_server['id'], 'ACTIVE')
        server = self.client.get_server(test_server['id'])
        self.assertEqual(server['status'], 'ACTIVE')
        hostname = server[self._host_key]
        params = {'host': hostname}
        body = self.client.list_servers(params)
        servers = body['servers']
        nonexistent_params = {'host': 'nonexistent_host'}
        nonexistent_body = self.client.list_servers(nonexistent_params)
        nonexistent_servers = nonexistent_body['servers']
        self.assertIn(test_server['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(test_server['id'],
                         map(lambda x: x['id'], nonexistent_servers))

    @test.attr(type='gate')
    @test.idempotent_id('ee8ae470-db70-474d-b752-690b7892cab1')
    def test_reset_state_server(self):
        # Reset server's state to 'error'
        self.client.reset_state(self.s1_id)

        # Verify server's state
        server = self.client.get_server(self.s1_id)
        self.assertEqual(server['status'], 'ERROR')

        # Reset server's state to 'active'
        self.client.reset_state(self.s1_id, state='active')

        # Verify server's state
        server = self.client.get_server(self.s1_id)
        self.assertEqual(server['status'], 'ACTIVE')

    @test.attr(type='gate')
    @decorators.skip_because(bug="1240043")
    @test.idempotent_id('31ff3486-b8a0-4f56-a6c0-aab460531db3')
    def test_get_server_diagnostics_by_admin(self):
        # Retrieve server diagnostics by admin user
        diagnostic = self.client.get_server_diagnostics(self.s1_id)
        basic_attrs = ['rx_packets', 'rx_errors', 'rx_drop',
                       'tx_packets', 'tx_errors', 'tx_drop',
                       'read_req', 'write_req', 'cpu', 'memory']
        for key in basic_attrs:
            self.assertIn(key, str(diagnostic.keys()))

    @test.attr(type='gate')
    @test.idempotent_id('682cb127-e5bb-4f53-87ce-cb9003604442')
    def test_rebuild_server_in_error_state(self):
        # The server in error state should be rebuilt using the provided
        # image and changed to ACTIVE state

        # resetting vm state require admin privilege
        self.client.reset_state(self.s1_id, state='error')
        rebuilt_server = self.non_admin_client.rebuild(
            self.s1_id, self.image_ref_alt)
        self.addCleanup(self.non_admin_client.wait_for_server_status,
                        self.s1_id, 'ACTIVE')
        self.addCleanup(self.non_admin_client.rebuild, self.s1_id,
                        self.image_ref)

        # Verify the properties in the initial response are correct
        self.assertEqual(self.s1_id, rebuilt_server['id'])
        rebuilt_image_id = rebuilt_server['image']['id']
        self.assertEqual(self.image_ref_alt, rebuilt_image_id)
        self.assertEqual(self.flavor_ref, rebuilt_server['flavor']['id'])
        self.non_admin_client.wait_for_server_status(rebuilt_server['id'],
                                                     'ACTIVE',
                                                     raise_on_error=False)
        # Verify the server properties after rebuilding
        server = self.non_admin_client.get_server(rebuilt_server['id'])
        rebuilt_image_id = server['image']['id']
        self.assertEqual(self.image_ref_alt, rebuilt_image_id)

    @test.attr(type='gate')
    @test.idempotent_id('7a1323b4-a6a2-497a-96cb-76c07b945c71')
    def test_reset_network_inject_network_info(self):
        # Reset Network of a Server
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.reset_network(server['id'])
        # Inject the Network Info into Server
        self.client.inject_network_info(server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('fdcd9b33-0903-4e00-a1f7-b5f6543068d6')
    def test_create_server_with_scheduling_hint(self):
        # Create a server with scheduler hints.
        hints = {
            'same_host': self.s1_id
        }
        self.create_test_server(sched_hints=hints,
                                wait_until='ACTIVE')
