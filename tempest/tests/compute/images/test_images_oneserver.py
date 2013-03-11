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


class ImagesOneServerTestJSON(base.BaseComputeTest):
    _interface = 'json'

    def tearDown(self):
        """Terminate test instances created after a test is executed."""
        for image_id in self.image_ids:
            self.client.delete_image(image_id)
            self.image_ids.remove(image_id)
        super(ImagesOneServerTestJSON, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(ImagesOneServerTestJSON, cls).setUpClass()
        cls.client = cls.images_client
        cls.servers_client = cls.servers_client
        resp, cls.server = cls.create_server(wait_until='ACTIVE')

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

    @attr(type='negative')
    @testtools.skip("Until Bug 1006725 is fixed")
    def test_create_image_specify_multibyte_character_image_name(self):
        # Return an error if the image name has multi-byte characters
        snapshot_name = rand_name('\xef\xbb\xbf')
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_image, self.server['id'],
                          snapshot_name)

    @attr(type='negative')
    @testtools.skip("Until Bug 1005423 is fixed")
    def test_create_image_specify_invalid_metadata(self):
        # Return an error when creating image with invalid metadata
        snapshot_name = rand_name('test-snap-')
        meta = {'': ''}
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          self.server['id'], snapshot_name, meta)

    @attr(type='negative')
    @testtools.skip("Until Bug 1005423 is fixed")
    def test_create_image_specify_metadata_over_limits(self):
        # Return an error when creating image with meta data over 256 chars
        snapshot_name = rand_name('test-snap-')
        meta = {'a' * 260: 'b' * 260}
        self.assertRaises(exceptions.OverLimit, self.client.create_image,
                          self.server['id'], snapshot_name, meta)

    @attr(type='negative')
    @testtools.skipUnless(compute.MULTI_USER,
                          'Need multiple users for this test.')
    def test_delete_image_of_another_tenant(self):
        # Return an error while trying to delete another tenant's image
        self.servers_client.wait_for_server_status(self.server['id'], 'ACTIVE')
        snapshot_name = rand_name('test-snap-')
        resp, body = self.client.create_image(self.server['id'], snapshot_name)
        image_id = parse_image_id(resp['location'])
        self.image_ids.append(image_id)
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        # Delete image
        self.assertRaises(exceptions.NotFound,
                          self.alt_client.delete_image, image_id)

    @attr(type='smoke')
    @testtools.skipUnless(compute.CREATE_IMAGE_ENABLED,
                          'Environment unable to create images.')
    def test_create_delete_image(self):

        # Create a new image
        name = rand_name('image')
        meta = {'image_type': 'test'}
        resp, body = self.client.create_image(self.server['id'], name, meta)
        self.assertEqual(202, resp.status)
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

    @attr(type='negative')
    @testtools.skipUnless(compute.MULTI_USER,
                          'Need multiple users for this test.')
    def test_create_image_for_server_in_another_tenant(self):
        # Creating image of another tenant's server should be return error

        snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.NotFound, self.alt_client.create_image,
                          self.server['id'], snapshot_name)

    @attr(type='negative')
    def test_create_second_image_when_first_image_is_being_saved(self):
        # Disallow creating another image when first image is being saved

        # Create first snapshot
        snapshot_name = rand_name('test-snap-')
        resp, body = self.client.create_image(self.server['id'],
                                              snapshot_name)
        self.assertEqual(202, resp.status)
        image_id = parse_image_id(resp['location'])
        self.image_ids.append(image_id)

        # Create second snapshot
        alt_snapshot_name = rand_name('test-snap-')
        self.assertRaises(exceptions.Duplicate, self.client.create_image,
                          self.server['id'], alt_snapshot_name)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

    @attr(type='negative')
    def test_create_image_specify_name_over_256_chars(self):
        # Return an error if snapshot name over 256 characters is passed

        snapshot_name = rand_name('a' * 260)
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          self.server['id'], snapshot_name)

    @attr(type='negative')
    def test_delete_image_that_is_not_yet_active(self):
        # Return an error while trying to delete an image what is creating

        snapshot_name = rand_name('test-snap-')
        resp, body = self.client.create_image(self.server['id'], snapshot_name)
        self.assertEqual(202, resp.status)
        image_id = parse_image_id(resp['location'])
        self.image_ids.append(image_id)

        # Do not wait, attempt to delete the image, ensure it's successful
        resp, body = self.client.delete_image(image_id)
        self.assertEqual('204', resp['status'])
        self.image_ids.remove(image_id)

        self.assertRaises(exceptions.NotFound, self.client.get_image, image_id)


class ImagesOneServerTestXML(ImagesOneServerTestJSON):
    _interface = 'xml'
