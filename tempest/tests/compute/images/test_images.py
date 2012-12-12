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

import nose
from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest.common.utils.data_utils import parse_image_id
from tempest.common.utils.data_utils import rand_name
import tempest.config
from tempest import exceptions
from tempest import openstack
from tempest.tests import compute
from tempest.tests.compute import base


class ImagesTestBase(object):

    def tearDown(self):
        """Terminate test instances created after a test is executed"""
        for server in self.servers:
            resp, body = self.servers_client.delete_server(server['id'])
            if resp['status'] == '204':
                self.servers.remove(server)
                self.servers_client.wait_for_server_termination(server['id'])

        for image_id in self.image_ids:
            self.client.delete_image(image_id)
            self.image_ids.remove(image_id)

    @attr(type='smoke')
    @unittest.skipUnless(compute.CREATE_IMAGE_ENABLED,
                         'Environment unable to create images.')
    def test_create_delete_image(self):
        """An image for the provided server should be created"""
        server_name = rand_name('server')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        # Create a new image
        name = rand_name('image')
        meta = {'image_type': 'test'}
        resp, body = self.client.create_image(server['id'], name, meta)
        image_id = parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        # Verify the image was created correctly
        resp, image = self.client.get_image(image_id)
        self.assertEqual(name, image['name'])
        self.assertEqual('test', image['metadata']['image_type'])

        # Verify minRAM and minDisk values are the same as the original image
        resp, original_image = self.client.get_image(self.image_ref)
        self.assertEqual(original_image['minRam'], image['minRam'])
        self.assertEqual(original_image['minDisk'], image['minDisk'])

        # Teardown
        self.client.delete_image(image['id'])
        self.servers_client.delete_server(server['id'])

    @attr(type='negative')
    def test_create_image_from_deleted_server(self):
        """An image should not be created if the server instance is removed """
        server_name = rand_name('server')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        # Delete server before trying to create server
        self.servers_client.delete_server(server['id'])

        try:
            # Create a new image after server is deleted
            name = rand_name('image')
            meta = {'image_type': 'test'}
            resp, body = self.client.create_image(server['id'], name, meta)

        except Exception:
            pass

        else:
            image_id = parse_image_id(resp['location'])
            self.client.wait_for_image_resp_code(image_id, 200)
            self.client.wait_for_image_status(image_id, 'ACTIVE')
            self.client.delete_image(image_id)
            self.fail("Should not create snapshot from deleted instance!")

    @attr(type='negative')
    def test_create_image_from_invalid_server(self):
        """An image should not be created with invalid server id"""
        try:
            # Create a new image with invalid server id
            name = rand_name('image')
            meta = {'image_type': 'test'}
            resp = {}
            resp['status'] = None
            resp, body = self.client.create_image('!@#$%^&*()', name, meta)

        except exceptions.NotFound:
            pass

        finally:
            if (resp['status'] is not None):
                image_id = parse_image_id(resp['location'])
                resp, _ = self.client.delete_image(image_id)
                self.fail("An image should not be created "
                          "with invalid server id")

    @attr(type='negative')
    @unittest.skipUnless(compute.MULTI_USER, 'Second user not configured')
    def test_create_image_for_server_in_another_tenant(self):
        """Creating image of another tenant's server should be return error"""
        server = self.create_server()

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.NotFound, self.alt_client.create_image,
                          server['id'], snapshot_name)

    @attr(type='negative')
    def test_create_image_when_server_is_building(self):
        """Return error when creating an image of a server that is building"""
        server_name = rand_name('test-vm-')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.servers.append(server)
        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          server['id'], snapshot_name)

    @unittest.skip("Until Bug 1039739 is fixed")
    @attr(type='negative')
    def test_create_image_when_server_is_rebooting(self):
        """Return error when creating an image of server that is rebooting"""
        server = self.create_server()
        self.servers_client.reboot(server['id'], 'HARD')

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          server['id'], snapshot_name)

    @attr(type='negative')
    def test_create_image_when_server_is_terminating(self):
        """Return an error when creating image of server that is terminating"""
        server = self.create_server()
        self.servers_client.delete_server(server['id'])

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          server['id'], snapshot_name)

    @attr(type='negative')
    def test_create_second_image_when_first_image_is_being_saved(self):
        """Disallow creating another image when first image is being saved"""
        server = self.create_server()

        try:
            # Create first snapshot
            snapshot_name = rand_name('test-snap-')
            resp, body = self.client.create_image(server['id'], snapshot_name)
            image_id = parse_image_id(resp['location'])
            self.image_ids.append(image_id)

            # Create second snapshot
            alt_snapshot_name = rand_name('test-snap-')
            self.client.create_image(server['id'], alt_snapshot_name)
        except exceptions.Duplicate:
            pass

        else:
            self.fail("Should allow creating an image when another image of"
                      "the server is still being saved")

    @attr(type='negative')
    @unittest.skip("Until Bug 1004564 is fixed")
    def test_create_image_specify_name_over_256_chars(self):
        """Return an error if snapshot name over 256 characters is passed"""
        server = self.create_server()

        try:
            snapshot_name = rand_name('a' * 260)
            self.assertRaises(exceptions.BadRequest, self.client.create_image,
                              server['id'], snapshot_name)
        except Exception:
            self.fail("Should return 400 Bad Request if image name is over 256"
                      " characters")

    @attr(type='negative')
    def test_create_image_specify_uuid_35_characters_or_less(self):
        """Return an error if Image ID passed is 35 characters or less"""
        try:
            snapshot_name = rand_name('test-snap-')
            test_uuid = ('a' * 35)
            self.assertRaises(exceptions.NotFound, self.client.create_image,
                              test_uuid, snapshot_name)
        except Exception:
            self.fail("Should return 404 Not Found if server uuid is 35"
                      " characters or less")

    @attr(type='negative')
    def test_create_image_specify_uuid_37_characters_or_more(self):
        """Return an error if Image ID passed is 37 characters or more"""
        try:
            snapshot_name = rand_name('test-snap-')
            test_uuid = ('a' * 37)
            self.assertRaises(exceptions.NotFound, self.client.create_image,
                              test_uuid, snapshot_name)
        except Exception:
            self.fail("Should return 404 Not Found if server uuid is 37"
                      " characters or more")

    @attr(type='negative')
    @unittest.skip("Until Bug 1006725 is fixed")
    def test_create_image_specify_multibyte_character_image_name(self):
        """Return an error if the image name has multi-byte characters"""
        server = self.create_server()

        try:
            snapshot_name = rand_name('\xef\xbb\xbf')
            self.assertRaises(exceptions.BadRequest,
                              self.client.create_image, server['id'],
                              snapshot_name)
        except Exception:
            self.fail("Should return 400 Bad Request if multi byte characters"
                      " are used for image name")

    @attr(type='negative')
    @unittest.skip("Until Bug 1005423 is fixed")
    def test_create_image_specify_invalid_metadata(self):
        """Return an error when creating image with invalid metadata"""
        server = self.create_server()

        try:
            snapshot_name = rand_name('test-snap-')
            meta = {'': ''}
            self.assertRaises(exceptions.BadRequest, self.client.create_image,
                              server['id'], snapshot_name, meta)

        except Exception:
            self.fail("Should raise 400 Bad Request if meta data is invalid")

    @attr(type='negative')
    @unittest.skip("Until Bug 1005423 is fixed")
    def test_create_image_specify_metadata_over_limits(self):
        """Return an error when creating image with meta data over 256 chars"""
        server = self.create_server()

        try:
            snapshot_name = rand_name('test-snap-')
            meta = {'a' * 260: 'b' * 260}
            self.assertRaises(exceptions.OverLimit, self.client.create_image,
                              server['id'], snapshot_name, meta)

        except Exception:
            self.fail("Should raise 413 Over Limit if meta data was too long")

    @attr(type='negative')
    def test_delete_image_with_invalid_image_id(self):
        """An image should not be deleted with invalid image id"""
        try:
            # Delete an image with invalid image id
            resp, _ = self.client.delete_image('!@$%^&*()')

        except exceptions.NotFound:
            pass

        else:
            self.fail("DELETE image request should rasie NotFound exception "
                      "when requested with invalid image")

    @attr(type='negative')
    def test_delete_non_existent_image(self):
        """Return an error while trying to delete a non-existent image"""

        non_existent_image_id = '11a22b9-12a9-5555-cc11-00ab112223fa'
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @attr(type='negative')
    def test_delete_image_blank_id(self):
        """Return an error while trying to delete an image with blank Id"""

        try:
            self.assertRaises(exceptions.NotFound, self.client.delete_image,
                              '')
        except Exception:
            self.fail("Did not return HTTP 404 NotFound for blank image id")

    @attr(type='negative')
    def test_delete_image_non_hex_string_id(self):
        """Return an error while trying to delete an image with non hex id"""

        image_id = '11a22b9-120q-5555-cc11-00ab112223gj'
        try:
            self.assertRaises(exceptions.NotFound, self.client.delete_image,
                              image_id)
        except Exception:
            self.fail("Did not return HTTP 404 NotFound for non hex image")

    @attr(type='negative')
    def test_delete_image_negative_image_id(self):
        """Return an error while trying to delete an image with negative id"""

        try:
            self.assertRaises(exceptions.NotFound, self.client.delete_image,
                              -1)
        except Exception:
            self.fail("Did not return HTTP 404 NotFound for negative image id")

    @attr(type='negative')
    def test_delete_image_id_is_over_35_character_limit(self):
        """Return an error while trying to delete image with id over limit"""

        try:
            self.assertRaises(exceptions.NotFound, self.client.delete_image,
                              '11a22b9-120q-5555-cc11-00ab112223gj-3fac')
        except Exception:
            self.fail("Did not return HTTP 404 NotFound for image id that "
                      "exceeds 35 character ID length limit")

    @attr(type='negative')
    @unittest.skipUnless(compute.MULTI_USER, 'Second user not configured')
    def test_delete_image_of_another_tenant(self):
        """Return an error while trying to delete another tenant's image"""

        server = self.create_server()

        snapshot_name = rand_name('test-snap-')
        resp, body = self.client.create_image(server['id'], snapshot_name)
        image_id = parse_image_id(resp['location'])
        self.image_ids.append(image_id)
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        # Delete image
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.delete_image, image_id)

    @attr(type='negative')
    def test_delete_image_that_is_not_yet_active(self):
        """Return an error while trying to delete an active that is creating"""

        server = self.create_server()

        snapshot_name = rand_name('test-snap-')
        resp, body = self.client.create_image(server['id'], snapshot_name)
        image_id = parse_image_id(resp['location'])
        self.image_ids.append(image_id)

        # Do not wait, attempt to delete the image, ensure it's successful
        resp, body = self.client.delete_image(image_id)
        self.assertEqual('204', resp['status'])
        self.image_ids.remove(image_id)

        self.assertRaises(exceptions.NotFound, self.client.get_image, image_id)


class ImagesTestJSON(base.BaseComputeTestJSON,
                     ImagesTestBase):
    def tearDown(self):
        ImagesTestBase.tearDown(self)

    @classmethod
    def setUpClass(cls):
        raise nose.SkipTest("Until Bug 1046870 is fixed")
        super(ImagesTestJSON, cls).setUpClass()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

        cls.image_ids = []

        if compute.MULTI_USER:
            if cls.config.compute.allow_tenant_isolation:
                creds = cls._get_isolated_creds()
                username, tenant_name, password = creds
                cls.alt_manager = openstack.Manager(username=username,
                                                    password=password,
                                                    tenant_name=tenant_name)
            else:
                # Use the alt_XXX credentials in the config file
                cls.alt_manager = openstack.AltManager()
            cls.alt_client = cls.alt_manager.images_client


class ImagesTestXML(base.BaseComputeTestXML,
                    ImagesTestBase):
    def tearDown(self):
        ImagesTestBase.tearDown(self)

    @classmethod
    def setUpClass(cls):
        raise nose.SkipTest("Until Bug 1046870 is fixed")
        super(ImagesTestXML, cls).setUpClass()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client

        cls.image_ids = []

        if compute.MULTI_USER:
            if cls.config.compute.allow_tenant_isolation:
                creds = cls._get_isolated_creds()
                username, tenant_name, password = creds
                cls.alt_manager = openstack.Manager(username=username,
                                                    password=password,
                                                    tenant_name=tenant_name)
            else:
                # Use the alt_XXX credentials in the config file
                cls.alt_manager = openstack.AltManager()
            cls.alt_client = cls.alt_manager.images_client
