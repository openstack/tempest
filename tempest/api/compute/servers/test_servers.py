# Copyright 2012 OpenStack Foundation
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

import testtools

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class ServersTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.idempotent_id('b92d5ec7-b1dd-44a2-87e4-45e888c46ef0')
    @testtools.skipUnless(CONF.compute_feature_enabled.
                          enable_instance_password,
                          'Instance password not available.')
    def test_create_server_with_admin_password(self):
        # If an admin password is provided on server creation, the server's
        # root password should be set to that password.
        server = self.create_test_server(adminPass='testpassword')
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, server['id'])

        # Verify the password is set correctly in the response
        self.assertEqual('testpassword', server['adminPass'])

    @decorators.idempotent_id('8fea6be7-065e-47cf-89b8-496e6f96c699')
    def test_create_with_existing_server_name(self):
        # Creating a server with a name that already exists is allowed

        # TODO(sdague): clear out try, we do cleanup one layer up
        server_name = data_utils.rand_name(
            self.__class__.__name__ + '-server')
        server = self.create_test_server(name=server_name,
                                         wait_until='ACTIVE')
        id1 = server['id']
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, id1)
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, id1)
        server = self.create_test_server(name=server_name,
                                         wait_until='ACTIVE')
        id2 = server['id']
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, id2)
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, id2)
        self.assertNotEqual(id1, id2, "Did not create a new server")
        server = self.client.show_server(id1)['server']
        name1 = server['name']
        server = self.client.show_server(id2)['server']
        name2 = server['name']
        self.assertEqual(name1, name2)

    @decorators.idempotent_id('f9e15296-d7f9-4e62-b53f-a04e89160833')
    def test_create_specify_keypair(self):
        # Specify a keypair while creating a server

        key_name = data_utils.rand_name('key')
        self.keypairs_client.create_keypair(name=key_name)
        self.addCleanup(self.keypairs_client.delete_keypair, key_name)
        self.keypairs_client.list_keypairs()
        server = self.create_test_server(key_name=key_name)
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')
        server = self.client.show_server(server['id'])['server']
        self.assertEqual(key_name, server['key_name'])

    def _update_server_name(self, server_id, status, prefix_name='server'):
        # The server name should be changed to the provided value
        new_name = data_utils.rand_name(prefix_name)

        # Update the server with a new name
        self.client.update_server(server_id,
                                  name=new_name)
        waiters.wait_for_server_status(self.client, server_id, status)

        # Verify the name of the server has changed
        server = self.client.show_server(server_id)['server']
        self.assertEqual(new_name, server['name'])
        return server

    @decorators.idempotent_id('5e6ccff8-349d-4852-a8b3-055df7988dd2')
    def test_update_server_name(self):
        # The server name should be changed to the provided value
        server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, server['id'])
        # Update instance name with non-ASCII characters
        prefix_name = u'\u00CD\u00F1st\u00E1\u00F1c\u00E9'
        self._update_server_name(server['id'], 'ACTIVE', prefix_name)

        # stop server and check server name update again
        self.client.stop_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'SHUTOFF')
        # Update instance name with non-ASCII characters
        updated_server = self._update_server_name(server['id'],
                                                  'SHUTOFF',
                                                  prefix_name)
        self.assertNotIn('progress', updated_server)

    @decorators.idempotent_id('89b90870-bc13-4b73-96af-f9d4f2b70077')
    def test_update_access_server_address(self):
        # The server's access addresses should reflect the provided values
        server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, server['id'])

        # Update the IPv4 and IPv6 access addresses
        self.client.update_server(server['id'],
                                  accessIPv4='1.1.1.1',
                                  accessIPv6='::babe:202:202')
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')

        # Verify the access addresses have been updated
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('1.1.1.1', server['accessIPv4'])
        self.assertEqual('::babe:202:202', server['accessIPv6'])

    @decorators.idempotent_id('38fb1d02-c3c5-41de-91d3-9bc2025a75eb')
    def test_create_server_with_ipv6_addr_only(self):
        # Create a server without an IPv4 address(only IPv6 address).
        server = self.create_test_server(accessIPv6='2001:2001::3')
        self.addCleanup(waiters.wait_for_server_termination,
                        self.servers_client, server['id'])
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.servers_client.delete_server, server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('2001:2001::3', server['accessIPv6'])


class ServerShowV247Test(base.BaseV2ComputeTest):
    min_microversion = '2.47'
    max_microversion = 'latest'

    @decorators.idempotent_id('88b0bdb2-494c-11e7-a919-92ebcb67fe33')
    def test_show_server(self):
        server = self.create_test_server()
        # All fields will be checked by API schema
        self.servers_client.show_server(server['id'])
