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

import StringIO

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import clients
from tempest import config
from tempest import test

CONF = config.CONF

LOG = logging.getLogger(__name__)


class AuthorizationTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(AuthorizationTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            raise cls.skipException('Glance is not available.')

    @classmethod
    def setup_credentials(cls):
        # No network resources required for this test
        cls.set_network_resources()
        super(AuthorizationTestJSON, cls).setup_credentials()
        if not cls.multi_user:
            msg = "Need >1 user"
            raise cls.skipException(msg)

        creds = cls.isolated_creds.get_alt_creds()
        cls.alt_manager = clients.Manager(credentials=creds)

    @classmethod
    def setup_clients(cls):
        super(AuthorizationTestJSON, cls).setup_clients()
        cls.client = cls.os.servers_client
        cls.images_client = cls.os.images_client
        cls.glance_client = cls.os.image_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_client = cls.os.security_groups_client

        cls.alt_client = cls.alt_manager.servers_client
        cls.alt_images_client = cls.alt_manager.images_client
        cls.alt_keypairs_client = cls.alt_manager.keypairs_client
        cls.alt_security_client = cls.alt_manager.security_groups_client

    @classmethod
    def resource_setup(cls):
        super(AuthorizationTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server = cls.client.get_server(server['id'])

        name = data_utils.rand_name('image')
        body = cls.glance_client.create_image(name=name,
                                              container_format='bare',
                                              disk_format='raw',
                                              is_public=False)
        image_id = body['id']
        image_file = StringIO.StringIO(('*' * 1024))
        body = cls.glance_client.update_image(image_id, data=image_file)
        cls.glance_client.wait_for_image_status(image_id, 'active')
        cls.image = cls.images_client.get_image(image_id)

        cls.keypairname = data_utils.rand_name('keypair')
        cls.keypairs_client.create_keypair(cls.keypairname)

        name = data_utils.rand_name('security')
        description = data_utils.rand_name('description')
        cls.security_group = cls.security_client.create_security_group(
            name, description)

        parent_group_id = cls.security_group['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        cls.rule = cls.security_client.create_security_group_rule(
            parent_group_id, ip_protocol, from_port, to_port)

    @classmethod
    def resource_cleanup(cls):
        if cls.multi_user:
            cls.images_client.delete_image(cls.image['id'])
            cls.keypairs_client.delete_keypair(cls.keypairname)
            cls.security_client.delete_security_group(cls.security_group['id'])
        super(AuthorizationTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    @test.idempotent_id('56816e4a-bd34-47b5-aee9-268c3efeb5d4')
    def test_get_server_for_alt_account_fails(self):
        # A GET request for a server on another user's account should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.get_server,
                          self.server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('fb8a4870-6d9d-44ad-8375-95d52e98d9f6')
    def test_delete_server_for_alt_account_fails(self):
        # A DELETE request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.delete_server,
                          self.server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('d792f91f-1d49-4eb5-b1ff-b229c4b9dc64')
    def test_update_server_for_alt_account_fails(self):
        # An update server request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.update_server,
                          self.server['id'], name='test')

    @test.attr(type='gate')
    @test.idempotent_id('488f24df-d7f7-4207-949a-f17fcb8e8769')
    def test_list_server_addresses_for_alt_account_fails(self):
        # A list addresses request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.list_addresses,
                          self.server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('00b442d0-2e72-40e7-9b1f-31772e36da01')
    def test_list_server_addresses_by_network_for_alt_account_fails(self):
        # A list address/network request for another user's server should fail
        server_id = self.server['id']
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.list_addresses_by_network, server_id,
                          'public')

    @test.attr(type='gate')
    @test.idempotent_id('cc90b35a-19f0-45d2-b680-2aabf934aa22')
    def test_list_servers_with_alternate_tenant(self):
        # A list on servers from one tenant should not
        # show on alternate tenant
        # Listing servers from alternate tenant
        alt_server_ids = []
        body = self.alt_client.list_servers()
        alt_server_ids = [s['id'] for s in body['servers']]
        self.assertNotIn(self.server['id'], alt_server_ids)

    @test.attr(type='gate')
    @test.idempotent_id('376dbc16-0779-4384-a723-752774799641')
    def test_change_password_for_alt_account_fails(self):
        # A change password request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.change_password,
                          self.server['id'], 'newpass')

    @test.attr(type='gate')
    @test.idempotent_id('14cb5ff5-f646-45ca-8f51-09081d6c0c24')
    def test_reboot_server_for_alt_account_fails(self):
        # A reboot request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.reboot,
                          self.server['id'], 'HARD')

    @test.attr(type='gate')
    @test.idempotent_id('8a0bce51-cd00-480b-88ba-dbc7d8408a37')
    def test_rebuild_server_for_alt_account_fails(self):
        # A rebuild request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.rebuild,
                          self.server['id'], self.image_ref_alt)

    @test.attr(type='gate')
    @test.idempotent_id('e4da647e-f982-4e61-9dad-1d1abebfb933')
    def test_resize_server_for_alt_account_fails(self):
        # A resize request for another user's server should fail
        self.assertRaises(lib_exc.NotFound, self.alt_client.resize,
                          self.server['id'], self.flavor_ref_alt)

    @test.attr(type='gate')
    @test.idempotent_id('a9fe8112-0ffa-4902-b061-f892bd5fe0d3')
    def test_create_image_for_alt_account_fails(self):
        # A create image request for another user's server should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.create_image,
                          self.server['id'], 'testImage')

    @test.attr(type='gate')
    @test.idempotent_id('95d445f6-babc-4f2e-aea3-aa24ec5e7f0d')
    def test_create_server_with_unauthorized_image(self):
        # Server creation with another user's image should fail
        self.assertRaises(lib_exc.BadRequest, self.alt_client.create_server,
                          'test', self.image['id'], self.flavor_ref)

    @test.attr(type='gate')
    @test.idempotent_id('acf8724b-142b-4044-82c3-78d31a533f24')
    def test_create_server_fails_when_tenant_incorrect(self):
        # A create server request should fail if the tenant id does not match
        # the current user
        # Change the base URL to impersonate another user
        self.alt_client.auth_provider.set_alt_auth_data(
            request_part='url',
            auth_data=self.client.auth_provider.auth_data
        )
        self.assertRaises(lib_exc.BadRequest,
                          self.alt_client.create_server, 'test',
                          self.image['id'], self.flavor_ref)

    @test.attr(type='gate')
    @test.idempotent_id('f03d1ded-7fd4-4d29-bc13-e2391f29c625')
    def test_create_keypair_in_analt_user_tenant(self):
        # A create keypair request should fail if the tenant id does not match
        # the current user
        # POST keypair with other user tenant
        k_name = data_utils.rand_name('keypair')
        try:
            # Change the base URL to impersonate another user
            self.alt_keypairs_client.auth_provider.set_alt_auth_data(
                request_part='url',
                auth_data=self.keypairs_client.auth_provider.auth_data
            )
            resp = {}
            resp['status'] = None
            self.assertRaises(lib_exc.BadRequest,
                              self.alt_keypairs_client.create_keypair, k_name)
        finally:
            # Next request the base_url is back to normal
            if (resp['status'] is not None):
                self.alt_keypairs_client.delete_keypair(k_name)
                LOG.error("Create keypair request should not happen "
                          "if the tenant id does not match the current user")

    @test.attr(type='gate')
    @test.idempotent_id('85bcdd8f-56b4-4868-ae56-63fbf6f7e405')
    def test_get_keypair_of_alt_account_fails(self):
        # A GET request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_keypairs_client.get_keypair,
                          self.keypairname)

    @test.attr(type='gate')
    @test.idempotent_id('6d841683-a8e0-43da-a1b8-b339f7692b61')
    def test_delete_keypair_of_alt_account_fails(self):
        # A DELETE request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_keypairs_client.delete_keypair,
                          self.keypairname)

    @test.attr(type='gate')
    @test.idempotent_id('fcb2e144-36e3-4dfb-9f9f-e72fcdec5656')
    def test_get_image_for_alt_account_fails(self):
        # A GET request for an image on another user's account should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.get_image, self.image['id'])

    @test.attr(type='gate')
    @test.idempotent_id('9facb962-f043-4a9d-b9ee-166a32dea098')
    def test_delete_image_for_alt_account_fails(self):
        # A DELETE request for another user's image should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.delete_image,
                          self.image['id'])

    @test.attr(type='gate')
    @test.idempotent_id('752c917e-83be-499d-a422-3559127f7d3c')
    def test_create_security_group_in_analt_user_tenant(self):
        # A create security group request should fail if the tenant id does not
        # match the current user
        # POST security group with other user tenant
        s_name = data_utils.rand_name('security')
        s_description = data_utils.rand_name('security')
        try:
            # Change the base URL to impersonate another user
            self.alt_security_client.auth_provider.set_alt_auth_data(
                request_part='url',
                auth_data=self.security_client.auth_provider.auth_data
            )
            resp = {}
            resp['status'] = None
            self.assertRaises(lib_exc.BadRequest,
                              self.alt_security_client.create_security_group,
                              s_name, s_description)
        finally:
            # Next request the base_url is back to normal
            if resp['status'] is not None:
                self.alt_security_client.delete_security_group(resp['id'])
                LOG.error("Create Security Group request should not happen if"
                          "the tenant id does not match the current user")

    @test.attr(type='gate')
    @test.idempotent_id('9db3590f-4d15-4e5f-985e-b28514919a6f')
    def test_get_security_group_of_alt_account_fails(self):
        # A GET request for another user's security group should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_security_client.get_security_group,
                          self.security_group['id'])

    @test.attr(type='gate')
    @test.idempotent_id('155387a5-2bbc-4acf-ab06-698dae537ea5')
    def test_delete_security_group_of_alt_account_fails(self):
        # A DELETE request for another user's security group should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_security_client.delete_security_group,
                          self.security_group['id'])

    @test.attr(type='gate')
    @test.idempotent_id('b2b76de0-210a-4089-b921-591c9ec552f6')
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
            self.assertRaises(lib_exc.BadRequest,
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

    @test.attr(type='gate')
    @test.idempotent_id('c6044177-37ef-4ce4-b12c-270ddf26d7da')
    def test_delete_security_group_rule_of_alt_account_fails(self):
        # A DELETE request for another user's security group rule
        # should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_security_client.delete_security_group_rule,
                          self.rule['id'])

    @test.attr(type='gate')
    @test.idempotent_id('c5f52351-53d9-4fc9-83e5-917f7f5e3d71')
    def test_set_metadata_of_alt_account_server_fails(self):
        # A set metadata for another user's server should fail
        req_metadata = {'meta1': 'data1', 'meta2': 'data2'}
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.set_server_metadata,
                          self.server['id'],
                          req_metadata)

    @test.attr(type='gate')
    @test.idempotent_id('fb6f51e9-df15-4939-898d-1aca38c258f0')
    def test_set_metadata_of_alt_account_image_fails(self):
        # A set metadata for another user's image should fail
        req_metadata = {'meta1': 'value1', 'meta2': 'value2'}
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.set_image_metadata,
                          self.image['id'], req_metadata)

    @test.attr(type='gate')
    @test.idempotent_id('dea1936a-473d-49f2-92ad-97bb7aded22e')
    def test_get_metadata_of_alt_account_server_fails(self):
        # A get metadata for another user's server should fail
        req_metadata = {'meta1': 'data1'}
        self.client.set_server_metadata(self.server['id'], req_metadata)
        self.addCleanup(self.client.delete_server_metadata_item,
                        self.server['id'], 'meta1')
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.get_server_metadata_item,
                          self.server['id'], 'meta1')

    @test.attr(type='gate')
    @test.idempotent_id('16b2d724-0d3b-4216-a9fa-97bd4d9cf670')
    def test_get_metadata_of_alt_account_image_fails(self):
        # A get metadata for another user's image should fail
        req_metadata = {'meta1': 'value1'}
        self.addCleanup(self.images_client.delete_image_metadata_item,
                        self.image['id'], 'meta1')
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.get_image_metadata_item,
                          self.image['id'], 'meta1')

    @test.attr(type='gate')
    @test.idempotent_id('79531e2e-e721-493c-8b30-a35db36fdaa6')
    def test_delete_metadata_of_alt_account_server_fails(self):
        # A delete metadata for another user's server should fail
        req_metadata = {'meta1': 'data1'}
        self.addCleanup(self.client.delete_server_metadata_item,
                        self.server['id'], 'meta1')
        self.client.set_server_metadata(self.server['id'], req_metadata)
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.delete_server_metadata_item,
                          self.server['id'], 'meta1')

    @test.attr(type='gate')
    @test.idempotent_id('a5175dcf-cef8-43d6-9b77-3cb707d62e94')
    def test_delete_metadata_of_alt_account_image_fails(self):
        # A delete metadata for another user's image should fail
        req_metadata = {'meta1': 'data1'}
        self.addCleanup(self.images_client.delete_image_metadata_item,
                        self.image['id'], 'meta1')
        self.images_client.set_image_metadata(self.image['id'],
                                              req_metadata)
        self.assertRaises(lib_exc.NotFound,
                          self.alt_images_client.delete_image_metadata_item,
                          self.image['id'], 'meta1')

    @test.attr(type='gate')
    @test.idempotent_id('b0c1e7a0-8853-40fd-8384-01f93d116cae')
    def test_get_console_output_of_alt_account_server_fails(self):
        # A Get Console Output for another user's server should fail
        self.assertRaises(lib_exc.NotFound,
                          self.alt_client.get_console_output,
                          self.server['id'], 10)
