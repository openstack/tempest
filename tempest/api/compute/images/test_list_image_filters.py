# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.test import attr


LOG = logging.getLogger(__name__)


class ListImageFiltersTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ListImageFiltersTestJSON, cls).setUpClass()
        if not cls.config.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.images_client
        cls.image_ids = []

        try:
            resp, cls.server1 = cls.create_test_server()
            resp, cls.server2 = cls.create_test_server(wait_until='ACTIVE')
            # NOTE(sdague) this is faster than doing the sync wait_util on both
            cls.servers_client.wait_for_server_status(cls.server1['id'],
                                                      'ACTIVE')

            # Create images to be used in the filter tests
            resp, body = cls.create_image_from_server(cls.server1['id'])
            cls.image1_id = data_utils.parse_image_id(resp['location'])
            cls.client.wait_for_image_status(cls.image1_id, 'ACTIVE')
            resp, cls.image1 = cls.client.get_image(cls.image1_id)

            # Servers have a hidden property for when they are being imaged
            # Performing back-to-back create image calls on a single
            # server will sometimes cause failures
            resp, body = cls.create_image_from_server(cls.server2['id'])
            cls.image3_id = data_utils.parse_image_id(resp['location'])
            cls.client.wait_for_image_status(cls.image3_id, 'ACTIVE')
            resp, cls.image3 = cls.client.get_image(cls.image3_id)

            resp, body = cls.create_image_from_server(cls.server1['id'])
            cls.image2_id = data_utils.parse_image_id(resp['location'])

            cls.client.wait_for_image_status(cls.image2_id, 'ACTIVE')
            resp, cls.image2 = cls.client.get_image(cls.image2_id)
        except Exception as exc:
            LOG.exception(exc)
            cls.tearDownClass()
            raise

    @attr(type=['negative', 'gate'])
    def test_get_image_not_existing(self):
        # Check raises a NotFound
        self.assertRaises(exceptions.NotFound, self.client.get_image,
                          "nonexistingimageid")

    @attr(type='gate')
    def test_list_images_filter_by_status(self):
        # The list of images should contain only images with the
        # provided status
        params = {'status': 'ACTIVE'}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_filter_by_name(self):
        # List of all images should contain the expected images filtered
        # by name
        params = {'name': self.image1['name']}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_filter_by_server_id(self):
        # The images should contain images filtered by server id
        params = {'server': self.server1['id']}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]),
                        "Failed to find image %s in images. Got images %s" %
                        (self.image1_id, images))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_filter_by_server_ref(self):
        # The list of servers should be filtered by server ref
        server_links = self.server2['links']

        # Try all server link types
        for link in server_links:
            params = {'server': link['href']}
            resp, images = self.client.list_images(params)

            self.assertFalse(any([i for i in images
                                  if i['id'] == self.image1_id]))
            self.assertFalse(any([i for i in images
                                  if i['id'] == self.image2_id]))
            self.assertTrue(any([i for i in images
                                 if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_filter_by_type(self):
        # The list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image_ref]))

    @attr(type='gate')
    def test_list_images_limit_results(self):
        # Verify only the expected number of results are returned
        params = {'limit': '1'}
        resp, images = self.client.list_images(params)
        # when _interface='xml', one element for images_links in images
        # ref: Question #224349
        self.assertEqual(1, len([x for x in images if 'id' in x]))

    @attr(type='gate')
    def test_list_images_filter_by_changes_since(self):
        # Verify only updated images are returned in the detailed list

        # Becoming ACTIVE will modify the updated time
        # Filter by the image's created time
        params = {'changes-since': self.image3['created']}
        resp, images = self.client.list_images(params)
        found = any([i for i in images if i['id'] == self.image3_id])
        self.assertTrue(found)

    @attr(type='gate')
    def test_list_images_with_detail_filter_by_status(self):
        # Detailed list of all images should only contain images
        # with the provided status
        params = {'status': 'ACTIVE'}
        resp, images = self.client.list_images_with_detail(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_with_detail_filter_by_name(self):
        # Detailed list of all images should contain the expected
        # images filtered by name
        params = {'name': self.image1['name']}
        resp, images = self.client.list_images_with_detail(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_with_detail_limit_results(self):
        # Verify only the expected number of results (with full details)
        # are returned
        params = {'limit': '1'}
        resp, images = self.client.list_images_with_detail(params)
        self.assertEqual(1, len(images))

    @attr(type='gate')
    def test_list_images_with_detail_filter_by_server_ref(self):
        # Detailed list of servers should be filtered by server ref
        server_links = self.server2['links']

        # Try all server link types
        for link in server_links:
            params = {'server': link['href']}
            resp, images = self.client.list_images_with_detail(params)

            self.assertFalse(any([i for i in images
                                  if i['id'] == self.image1_id]))
            self.assertFalse(any([i for i in images
                                  if i['id'] == self.image2_id]))
            self.assertTrue(any([i for i in images
                                 if i['id'] == self.image3_id]))

    @attr(type='gate')
    def test_list_images_with_detail_filter_by_type(self):
        # The detailed list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        resp, images = self.client.list_images_with_detail(params)
        resp, image4 = self.client.get_image(self.image_ref)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image_ref]))

    @attr(type='gate')
    def test_list_images_with_detail_filter_by_changes_since(self):
        # Verify an update image is returned

        # Becoming ACTIVE will modify the updated time
        # Filter by the image's created time
        params = {'changes-since': self.image1['created']}
        resp, images = self.client.list_images_with_detail(params)
        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))

    @attr(type=['negative', 'gate'])
    def test_get_nonexistant_image(self):
        # Negative test: GET on non-existent image should fail
        self.assertRaises(exceptions.NotFound, self.client.get_image, 999)


class ListImageFiltersTestXML(ListImageFiltersTestJSON):
    _interface = 'xml'
