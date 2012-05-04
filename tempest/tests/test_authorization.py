import unittest2 as unittest

from nose.plugins.attrib import attr
from nose.tools import raises

from tempest import openstack
from tempest.common.utils.data_utils import rand_name, parse_image_id
from tempest import exceptions
from tempest.tests import utils


class AuthorizationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.images_client = cls.os.images_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.compute.image_ref
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.image_ref_alt = cls.config.compute.image_ref_alt
        cls.flavor_ref_alt = cls.config.compute.flavor_ref_alt

        # Verify the second user is not the same as the first and is configured
        cls.user1 = cls.config.compute.username
        cls.user2 = cls.config.compute.alt_username
        cls.user2_password = cls.config.compute.alt_password
        cls.user2_tenant_name = cls.config.compute.alt_tenant_name
        cls.multi_user = False

        if  (cls.user2 != None and cls.user1 != cls.user2
            and cls.user2_password != None
            and cls.user2_tenant_name != None):

            try:
                cls.other_manager = openstack.AltManager()
                cls.other_client = cls.other_manager.servers_client
                cls.other_images_client = cls.other_manager.images_client
            except exceptions.AuthenticationFailure:
                # multi_user is already set to false, just fall through
                pass
            else:
                cls.multi_user = True

                name = rand_name('server')
                resp, server = cls.client.create_server(name, cls.image_ref,
                                                        cls.flavor_ref)
                cls.client.wait_for_server_status(server['id'], 'ACTIVE')
                resp, cls.server = cls.client.get_server(server['id'])

                name = rand_name('image')
                resp, body = cls.client.create_image(server['id'], name)
                image_id = parse_image_id(resp['location'])
                cls.images_client.wait_for_image_resp_code(image_id, 200)
                cls.images_client.wait_for_image_status(image_id, 'ACTIVE')
                resp, cls.image = cls.images_client.get_image(image_id)

    @classmethod
    def tearDownClass(cls):
        if cls.multi_user:
            cls.client.delete_server(cls.server['id'])
            cls.images_client.delete_image(cls.image['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_get_server_for_other_account_fails(self):
        """A GET request for a server on another user's account should fail"""
        self.other_client.get_server(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_delete_server_for_other_account_fails(self):
        """A DELETE request for another user's server should fail"""
        self.other_client.delete_server(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_update_server_for_other_account_fails(self):
        """An update server request for another user's server should fail"""
        self.other_client.update_server(self.server['id'], name='test')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_list_server_addresses_for_other_account_fails(self):
        """A list addresses request for another user's server should fail"""
        self.other_client.list_addresses(self.server['id'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_list_server_addresses_by_network_for_other_account_fails(self):
        """
        A list address/network request for another user's server should fail
        """
        server_id = self.server['id']
        self.other_client.list_addresses_by_network(server_id, 'public')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_change_password_for_other_account_fails(self):
        """A change password request for another user's server should fail"""
        self.other_client.change_password(self.server['id'], 'newpass')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_reboot_server_for_other_account_fails(self):
        """A reboot request for another user's server should fail"""
        self.other_client.reboot(self.server['id'], 'HARD')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_rebuild_server_for_other_account_fails(self):
        """A rebuild request for another user's server should fail"""
        self.other_client.rebuild(self.server['id'], self.image_ref_alt)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_resize_server_for_other_account_fails(self):
        """A resize request for another user's server should fail"""
        self.other_client.resize(self.server['id'], self.flavor_ref_alt)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_create_image_for_other_account_fails(self):
        """A create image request for another user's server should fail"""
        self.other_images_client.create_image(self.server['id'], 'testImage')

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_create_server_with_unauthorized_image(self):
        """Server creation with another user's image should fail"""
        self.other_client.create_server('test', self.image['id'],
                                         self.flavor_ref)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    @utils.skip_unless_attr('multi_user', 'Second user not configured')
    def test_create_server_fails_when_tenant_incorrect(self):
        """
        A create server request should fail if the tenant id does not match
        the current user
        """
        saved_base_url = self.other_client.base_url
        try:
            # Change the base URL to impersonate another user
            self.other_client.base_url = self.client.base_url
            self.other_client.create_server('test', self.image['id'],
                                                    self.flavor_ref)
        finally:
            # Reset the base_url...
            self.other_client.base_url = saved_base_url
