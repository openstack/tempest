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

from tempest.api.compute import base
from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.test import attr

CONF = config.CONF

LOG = logging.getLogger(__name__)


class AuthorizationTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        # No network resources required for this test
        cls.set_network_resources()
        super(AuthorizationTestJSON, cls).setUpClass()
        if not cls.multi_user:
            msg = "Need >1 user"
            raise cls.skipException(msg)
        cls.client = cls.os.servers_client
        cls.images_client = cls.os.images_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_client = cls.os.security_groups_client

        if CONF.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_alt_creds()
            username, tenant_name, password = creds
            cls.alt_manager = clients.Manager(username=username,
                                              password=password,
                                              tenant_name=tenant_name)
        else:
            # Use the alt_XXX credentials in the config file
            cls.alt_manager = clients.AltManager()

        cls.alt_client = cls.alt_manager.servers_client
        cls.alt_images_client = cls.alt_manager.images_client
        cls.alt_keypairs_client = cls.alt_manager.keypairs_client
        cls.alt_security_client = cls.alt_manager.security_groups_client

        resp, server = cls.create_test_server(wait_until='ACTIVE')
        resp, cls.server = cls.client.get_server(server['id'])

        name = data_utils.rand_name('image')
        resp, body = cls.client.create_image(server['id'], name)
        image_id = data_utils.parse_image_id(resp['location'])
        cls.images_client.wait_for_image_status(image_id, 'ACTIVE')
        resp, cls.image = cls.images_client.get_image(image_id)

        cls.keypairname = data_utils.rand_name('keypair')
        resp, keypair = \
            cls.keypairs_client.create_keypair(cls.keypairname)

        name = data_utils.rand_name('security')
        description = data_utils.rand_name('description')
        resp, cls.security_group = cls.security_client.create_security_group(
            name, description)

        parent_group_id = cls.security_group['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        resp, cls.rule = cls.security_client.create_security_group_rule(
            parent_group_id, ip_protocol, from_port, to_port)

    @classmethod
    def tearDownClass(cls):
        if cls.multi_user:
            cls.images_client.delete_image(cls.image['id'])
            cls.keypairs_client.delete_keypair(cls.keypairname)
            cls.security_client.delete_security_group(cls.security_group['id'])
        super(AuthorizationTestJSON, cls).tearDownClass()

    @attr(type='gate')
    def test_get_server_for_alt_account_fails(self):
        # A GET request for a server on another user's account should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.get_server,
                          self.server['id'])

    @attr(type='gate')
    def test_delete_server_for_alt_account_fails(self):
        # A DELETE request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.delete_server,
                          self.server['id'])

    @attr(type='gate')
    def test_update_server_for_alt_account_fails(self):
        # An update server request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.update_server,
                          self.server['id'], name='test')

    @attr(type='gate')
    def test_list_server_addresses_for_alt_account_fails(self):
        # A list addresses request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.list_addresses,
                          self.server['id'])

    @attr(type='gate')
    def test_list_server_addresses_by_network_for_alt_account_fails(self):
        # A list address/network request for another user's server should fail
        server_id = self.server['id']
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.list_addresses_by_network, server_id,
                          'public')

    @attr(type='gate')
    def test_list_servers_with_alternate_tenant(self):
        # A list on servers from one tenant should not
        # show on alternate tenant
        # Listing servers from alternate tenant
        alt_server_ids = []
        resp, body = self.alt_client.list_servers()
        alt_server_ids = [s['id'] for s in body['servers']]
        self.assertNotIn(self.server['id'], alt_server_ids)

    @attr(type='gate')
    def test_change_password_for_alt_account_fails(self):
        # A change password request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.change_password,
                          self.server['id'], 'newpass')

    @attr(type='gate')
    def test_reboot_server_for_alt_account_fails(self):
        # A reboot request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.reboot,
                          self.server['id'], 'HARD')

    @attr(type='gate')
    def test_rebuild_server_for_alt_account_fails(self):
        # A rebuild request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.rebuild,
                          self.server['id'], self.image_ref_alt)

    @attr(type='gate')
    def test_resize_server_for_alt_account_fails(self):
        # A resize request for another user's server should fail
        self.assertRaises(exceptions.NotFound, self.alt_client.resize,
                          self.server['id'], self.flavor_ref_alt)

    @attr(type='gate')
    def test_create_image_for_alt_account_fails(self):
        # A create image request for another user's server should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.create_image,
                          self.server['id'], 'testImage')

    @attr(type='gate')
    def test_create_server_with_unauthorized_image(self):
        # Server creation with another user's image should fail
        self.assertRaises(exceptions.BadRequest, self.alt_client.create_server,
                          'test', self.image['id'], self.flavor_ref)

    @attr(type='gate')
    def test_create_server_fails_when_tenant_incorrect(self):
        # A create server request should fail if the tenant id does not match
        # the current user
        # Change the base URL to impersonate another user
        self.alt_client.auth_provider.set_alt_auth_data(
            request_part='url',
            auth_data=self.client.auth_provider.auth_data
        )
        self.assertRaises(exceptions.BadRequest,
                          self.alt_client.create_server, 'test',
                          self.image['id'], self.flavor_ref)

    @attr(type='gate')
    def test_create_keypair_in_analt_user_tenant(self):
        # A create keypair request should fail if the tenant id does not match
        # the current user
        # POST keypair with other user tenant
        k_name = data_utils.rand_name('keypair-')
        try:
            # Change the base URL to impersonate another user
            self.alt_keypairs_client.auth_provider.set_alt_auth_data(
                request_part='url',
                auth_data=self.keypairs_client.auth_provider.auth_data
            )
            resp = {}
            resp['status'] = None
            self.assertRaises(exceptions.BadRequest,
                              self.alt_keypairs_client.create_keypair, k_name)
        finally:
            # Next request the base_url is back to normal
            if (resp['status'] is not None):
                resp, _ = self.alt_keypairs_client.delete_keypair(k_name)
                LOG.error("Create keypair request should not happen "
                          "if the tenant id does not match the current user")

    @attr(type='gate')
    def test_get_keypair_of_alt_account_fails(self):
        # A GET request for another user's keypair should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_keypairs_client.get_keypair,
                          self.keypairname)

    @attr(type='gate')
    def test_delete_keypair_of_alt_account_fails(self):
        # A DELETE request for another user's keypair should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_keypairs_client.delete_keypair,
                          self.keypairname)

    @attr(type='gate')
    def test_get_image_for_alt_account_fails(self):
        # A GET request for an image on another user's account should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.get_image, self.image['id'])

    @attr(type='gate')
    def test_delete_image_for_alt_account_fails(self):
        # A DELETE request for another user's image should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.delete_image,
                          self.image['id'])

    @attr(type='gate')
    def test_create_security_group_in_analt_user_tenant(self):
        # A create security group request should fail if the tenant id does not
        # match the current user
        # POST security group with other user tenant
        s_name = data_utils.rand_name('security-')
        s_description = data_utils.rand_name('security')
        try:
            # Change the base URL to impersonate another user
            self.alt_security_client.auth_provider.set_alt_auth_data(
                request_part='url',
                auth_data=self.security_client.auth_provider.auth_data
            )
            resp = {}
            resp['status'] = None
            self.assertRaises(exceptions.BadRequest,
                              self.alt_security_client.create_security_group,
                              s_name, s_description)
        finally:
            # Next request the base_url is back to normal
            if resp['status'] is not None:
                self.alt_security_client.delete_security_group(resp['id'])
                LOG.error("Create Security Group request should not happen if"
                          "the tenant id does not match the current user")

    @attr(type='gate')
    def test_get_security_group_of_alt_account_fails(self):
        # A GET request for another user's security group should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_security_client.get_security_group,
                          self.security_group['id'])

    @attr(type='gate')
    def test_delete_security_group_of_alt_account_fails(self):
        # A DELETE request for another user's security group should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_security_client.delete_security_group,
                          self.security_group['id'])

    @attr(type='gate')
    def test_create_security_group_rule_in_analt_user_tenant(self):
        # A create security group rule request should fail if the tenant id
        # does not match the current user
        # POST security group rule with other user tenant
        parent_group_id = self.security_group['id']
        ip_protocol = 'icmp'
        from_port = -1
        to_port = -1
        try:
            # Change the base URL to impersonate another user
            self.alt_security_client.auth_provider.set_alt_auth_data(
                request_part='url',
                auth_data=self.security_client.auth_provider.auth_data
            )
            resp = {}
            resp['status'] = None
            self.assertRaises(exceptions.BadRequest,
                              self.alt_security_client.
                              create_security_group_rule,
                              parent_group_id, ip_protocol, from_port,
                              to_port)
        finally:
            # Next request the base_url is back to normal
            if resp['status'] is not None:
                self.alt_security_client.delete_security_group_rule(resp['id'])
                LOG.error("Create security group rule request should not "
                          "happen if the tenant id does not match the"
                          " current user")

    @attr(type='gate')
    def test_delete_security_group_rule_of_alt_account_fails(self):
        # A DELETE request for another user's security group rule
        # should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_security_client.delete_security_group_rule,
                          self.rule['id'])

    @attr(type='gate')
    def test_set_metadata_of_alt_account_server_fails(self):
        # A set metadata for another user's server should fail
        req_metadata = {'meta1': 'data1', 'meta2': 'data2'}
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.set_server_metadata,
                          self.server['id'],
                          req_metadata)

    @attr(type='gate')
    def test_set_metadata_of_alt_account_image_fails(self):
        # A set metadata for another user's image should fail
        req_metadata = {'meta1': 'value1', 'meta2': 'value2'}
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.set_image_metadata,
                          self.image['id'], req_metadata)

    @attr(type='gate')
    def test_get_metadata_of_alt_account_server_fails(self):
        # A get metadata for another user's server should fail
        req_metadata = {'meta1': 'data1'}
        self.client.set_server_metadata(self.server['id'], req_metadata)
        self.addCleanup(self.client.delete_server_metadata_item,
                        self.server['id'], 'meta1')
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.get_server_metadata_item,
                          self.server['id'], 'meta1')

    @attr(type='gate')
    def test_get_metadata_of_alt_account_image_fails(self):
        # A get metadata for another user's image should fail
        req_metadata = {'meta1': 'value1'}
        self.addCleanup(self.images_client.delete_image_metadata_item,
                        self.image['id'], 'meta1')
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.get_image_metadata_item,
                          self.image['id'], 'meta1')

    @attr(type='gate')
    def test_delete_metadata_of_alt_account_server_fails(self):
        # A delete metadata for another user's server should fail
        req_metadata = {'meta1': 'data1'}
        self.addCleanup(self.client.delete_server_metadata_item,
                        self.server['id'], 'meta1')
        self.client.set_server_metadata(self.server['id'], req_metadata)
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.delete_server_metadata_item,
                          self.server['id'], 'meta1')

    @attr(type='gate')
    def test_delete_metadata_of_alt_account_image_fails(self):
        # A delete metadata for another user's image should fail
        req_metadata = {'meta1': 'data1'}
        self.addCleanup(self.images_client.delete_image_metadata_item,
                        self.image['id'], 'meta1')
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        self.assertRaises(exceptions.NotFound,
                          self.alt_images_client.delete_image_metadata_item,
                          self.image['id'], 'meta1')

    @attr(type='gate')
    def test_get_console_output_of_alt_account_server_fails(self):
        # A Get Console Output for another user's server should fail
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.get_console_output,
                          self.server['id'], 10)


class AuthorizationTestXML(AuthorizationTestJSON):
    _interface = 'xml'
