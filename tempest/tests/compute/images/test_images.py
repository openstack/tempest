# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest import clients
from tempest.common.utils.data_utils import parse_image_id
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests import compute
from tempest.tests.compute import base


class ImagesTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ImagesTestJSON, cls).setUpClass()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

        cls.image_ids = []

        if compute.MULTI_USER:
            if cls.config.compute.allow_tenant_isolation:
                creds = cls._get_isolated_creds()
                username, tenant_name, password = creds
                cls.alt_manager = clients.Manager(username=username,
                                                  password=password,
                                                  tenant_name=tenant_name)
            else:
                # Use the alt_XXX credentials in the config file
                cls.alt_manager = clients.AltManager()
            cls.alt_client = cls.alt_manager.images_client

    def tearDown(self):
        """Terminate test instances created after a test is executed."""
        for image_id in self.image_ids:
            self.client.delete_image(image_id)
            self.image_ids.remove(image_id)
        super(ImagesTestJSON, self).tearDown()

    def __create_image__(self, server_id, name, meta=None):
        resp, body = self.client.create_image(server_id, name, meta)
        image_id = parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        self.image_ids.append(image_id)
        return resp, body

    @attr(type='negative')
    def test_create_image_from_deleted_server(self):
        # An image should not be created if the server instance is removed
        resp, server = self.create_server(wait_until='ACTIVE')

        # Delete server before trying to create server
        self.servers_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])
        # Create a new image after server is deleted
        name = rand_name('image')
        meta = {'image_type': 'test'}
        self.assertRaises(exceptions.NotFound,
                          self.__create_image__,
                          server['id'], name, meta)

    @attr(type='negative')
    def test_create_image_from_invalid_server(self):
        # An image should not be created with invalid server id
        # Create a new image with invalid server id
        name = rand_name('image')
        meta = {'image_type': 'test'}
        resp = {}
        resp['status'] = None
        self.assertRaises(exceptions.NotFound, self.__create_image__,
                          '!@#$%^&*()', name, meta)

    @attr(type='negative')
    def test_create_image_when_server_is_terminating(self):
        # Return an error when creating image of server that is terminating
        resp, server = self.create_server(wait_until='ACTIVE')
        self.servers_client.delete_server(server['id'])

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          server['id'], snapshot_name)

    @testtools.skip("Until Bug #1039739 is fixed")
    @attr(type='negative')
    def test_create_image_when_server_is_rebooting(self):
        # Return error when creating an image of server that is rebooting
        resp, server = self.create_server()
        self.servers_client.reboot(server['id'], 'HARD')

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          server['id'], snapshot_name)

    @attr(type='negative')
    def test_create_image_specify_uuid_35_characters_or_less(self):
        # Return an error if Image ID passed is 35 characters or less
        snapshot_name = rand_name('test-snap-')
        test_uuid = ('a' * 35)
        self.assertRaises(exceptions.NotFound, self.client.create_image,
                          test_uuid, snapshot_name)

    @attr(type='negative')
    def test_create_image_specify_uuid_37_characters_or_more(self):
        # Return an error if Image ID passed is 37 characters or more
        snapshot_name = rand_name('test-snap-')
        test_uuid = ('a' * 37)
        self.assertRaises(exceptions.NotFound, self.client.create_image,
                          test_uuid, snapshot_name)

    @attr(type='negative')
    def test_delete_image_with_invalid_image_id(self):
        # An image should not be deleted with invalid image id
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          '!@$%^&*()')

    @attr(type='negative')
    def test_delete_non_existent_image(self):
        # Return an error while trying to delete a non-existent image

        non_existent_image_id = '11a22b9-12a9-5555-cc11-00ab112223fa'
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @attr(type='negative')
    def test_delete_image_blank_id(self):
        # Return an error while trying to delete an image with blank Id
        self.assertRaises(exceptions.NotFound, self.client.delete_image, '')

    @attr(type='negative')
    def test_delete_image_non_hex_string_id(self):
        # Return an error while trying to delete an image with non hex id
        image_id = '11a22b9-120q-5555-cc11-00ab112223gj'
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          image_id)

    @attr(type='negative')
    def test_delete_image_negative_image_id(self):
        # Return an error while trying to delete an image with negative id
        self.assertRaises(exceptions.NotFound, self.client.delete_image, -1)

    @attr(type='negative')
    def test_delete_image_id_is_over_35_character_limit(self):
        # Return an error while trying to delete image with id over limit
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          '11a22b9-120q-5555-cc11-00ab112223gj-3fac')


class ImagesTestXML(ImagesTestJSON):
    _interface = 'xml'
