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
        self.addCleanup(self.delete_server, server['id'])

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
        self.addCleanup(self.delete_server, id1)
        server = self.create_test_server(name=server_name,
                                         wait_until='ACTIVE')
        id2 = server['id']
        self.addCleanup(self.delete_server, id2)
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
        server = self.create_test_server(key_name=key_name,
                                         wait_until='ACTIVE')
        self.addCleanup(self.delete_server, server['id'])
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
        self.addCleanup(self.delete_server, server['id'])
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
        self.addCleanup(self.delete_server, server['id'])

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
        server = self.create_test_server(accessIPv6='2001:2001::3',
                                         wait_until='ACTIVE')
        self.addCleanup(self.delete_server, server['id'])
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('2001:2001::3', server['accessIPv6'])

    @decorators.related_bug('1730756')
    @decorators.idempotent_id('defbaca5-d611-49f5-ae21-56ee25d2db49')
    def test_create_server_specify_multibyte_character_name(self):
        # prefix character is:
        # http://unicode.org/cldr/utility/character.jsp?a=20A1

        # We use a string with 3 byte utf-8 character due to nova
        # will return 400(Bad Request) if we attempt to send a name which has
        # 4 byte utf-8 character.
        utf8_name = data_utils.rand_name(b'\xe2\x82\xa1'.decode('utf-8'))
        self.create_test_server(name=utf8_name, wait_until='ACTIVE')


class ServerShowV247Test(base.BaseV2ComputeTest):
    min_microversion = '2.47'
    max_microversion = 'latest'

    # NOTE(gmann): This test tests the server APIs response schema
    # Along with 2.47 microversion schema this test class tests the
    # other microversions 2.9, 2.19 and 2.26 server APIs response schema
    # also. 2.47 APIs schema are on top of 2.9->2.19->2.26 schema so
    # below tests cover all of the schema.

    @decorators.idempotent_id('88b0bdb2-494c-11e7-a919-92ebcb67fe33')
    def test_show_server(self):
        server = self.create_test_server()
        # All fields will be checked by API schema
        self.servers_client.show_server(server['id'])

    @decorators.idempotent_id('8de397c2-57d0-4b90-aa30-e5d668f21a8b')
    def test_update_rebuild_list_server(self):
        server = self.create_test_server()
        # Checking update API response schema
        self.servers_client.update_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')
        # Checking rebuild API response schema
        self.servers_client.rebuild_server(server['id'], self.image_ref_alt)
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')
        # Checking list details API response schema
        self.servers_client.list_servers(detail=True)


class ServerShowV263Test(base.BaseV2ComputeTest):
    min_microversion = '2.63'
    max_microversion = 'latest'

    @decorators.idempotent_id('71b8e3d5-11d2-494f-b917-b094a4afed3c')
    def test_show_update_rebuild_list_server(self):
        trusted_certs = ['test-cert-1', 'test-cert-2']
        server = self.create_test_server(
            trusted_image_certificates=trusted_certs,
            wait_until='ACTIVE')

        # Check show API response schema
        self.servers_client.show_server(server['id'])['server']

        # Check update API response schema
        self.servers_client.update_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

        # Check rebuild API response schema
        self.servers_client.rebuild_server(server['id'], self.image_ref_alt)
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

        # Check list details API response schema
        params = {'trusted_image_certificates': trusted_certs}
        servers = self.servers_client.list_servers(
            detail=True, **params)['servers']
        self.assertNotEmpty(servers)
