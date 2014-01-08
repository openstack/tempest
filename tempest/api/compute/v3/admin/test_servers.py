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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr
from tempest.test import skip_because


class ServersAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Servers API using admin privileges
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServersAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.servers_client
        cls.non_admin_client = cls.servers_client
        cls.flavors_client = cls.os_adm.flavors_client

        cls.s1_name = data_utils.rand_name('server')
        resp, server = cls.create_test_server(name=cls.s1_name,
                                              wait_until='ACTIVE')
        cls.s1_id = server['id']

        cls.s2_name = data_utils.rand_name('server')
        resp, server = cls.create_test_server(name=cls.s2_name,
                                              wait_until='ACTIVE')

    def _get_unused_flavor_id(self):
        flavor_id = data_utils.rand_int_id(start=1000)
        while True:
            try:
                resp, body = self.flavors_client.get_flavor_details(flavor_id)
            except exceptions.NotFound:
                break
            flavor_id = data_utils.rand_int_id(start=1000)
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
        _, server = self.create_test_server()
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])
        self.servers_client.wait_for_server_termination(server['id'])

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

    @attr(type='gate')
    @skip_because(bug="1240043")
    def test_get_server_diagnostics_by_admin(self):
        # Retrieve server diagnostics by admin user
        resp, diagnostic = self.client.get_server_diagnostics(self.s1_id)
        self.assertEqual(200, resp.status)
        basic_attrs = ['rx_packets', 'rx_errors', 'rx_drop',
                       'tx_packets', 'tx_errors', 'tx_drop',
                       'read_req', 'write_req', 'cpu', 'memory']
        for key in basic_attrs:
            self.assertIn(key, str(diagnostic.keys()))

    @attr(type='gate')
    def test_rebuild_server_in_error_state(self):
        # The server in error state should be rebuilt using the provided
        # image and changed to ACTIVE state

        # resetting vm state require admin priviledge
        resp, server = self.client.reset_state(self.s1_id, state='error')
        self.assertEqual(202, resp.status)
        resp, rebuilt_server = self.non_admin_client.rebuild(
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
        resp, server = self.non_admin_client.get_server(rebuilt_server['id'])
        rebuilt_image_id = server['image']['id']
        self.assertEqual(self.image_ref_alt, rebuilt_image_id)


class ServersAdminTestXML(ServersAdminTestJSON):
    _interface = 'xml'
