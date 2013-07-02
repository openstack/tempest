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
from tempest.common.utils.data_utils import rand_name
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

        cls.s1_name = rand_name('server')
        resp, server = cls.create_server(name=cls.s1_name,
                                         wait_until='ACTIVE')
        cls.s2_name = rand_name('server')
        resp, server = cls.create_server(name=cls.s2_name,
                                         wait_until='ACTIVE')

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


class ServersAdminTestXML(ServersAdminTestJSON):
    _interface = 'xml'
