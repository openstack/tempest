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

from nose.plugins.attrib import attr

from tempest.common.utils.data_utils import parse_image_id
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute.base import BaseComputeTest


class ListImageFiltersTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ListImageFiltersTest, cls).setUpClass()
        cls.client = cls.images_client

        name = rand_name('server')
        resp, cls.server1 = cls.servers_client.create_server(name,
                                                             cls.image_ref,
                                                             cls.flavor_ref)
        name = rand_name('server')
        resp, cls.server2 = cls.servers_client.create_server(name,
                                                             cls.image_ref,
                                                             cls.flavor_ref)
        cls.servers_client.wait_for_server_status(cls.server1['id'], 'ACTIVE')
        cls.servers_client.wait_for_server_status(cls.server2['id'], 'ACTIVE')

        # Create images to be used in the filter tests
        image1_name = rand_name('image')
        resp, body = cls.client.create_image(cls.server1['id'], image1_name)
        cls.image1_id = parse_image_id(resp['location'])
        cls.client.wait_for_image_resp_code(cls.image1_id, 200)
        cls.client.wait_for_image_status(cls.image1_id, 'ACTIVE')
        resp, cls.image1 = cls.client.get_image(cls.image1_id)

        # Servers have a hidden property for when they are being imaged
        # Performing back-to-back create image calls on a single
        # server will sometimes cause failures
        image3_name = rand_name('image')
        resp, body = cls.client.create_image(cls.server2['id'], image3_name)
        cls.image3_id = parse_image_id(resp['location'])
        cls.client.wait_for_image_resp_code(cls.image3_id, 200)
        cls.client.wait_for_image_status(cls.image3_id, 'ACTIVE')
        resp, cls.image3 = cls.client.get_image(cls.image3_id)

        image2_name = rand_name('image')
        resp, body = cls.client.create_image(cls.server1['id'], image2_name)
        cls.image2_id = parse_image_id(resp['location'])
        cls.client.wait_for_image_resp_code(cls.image2_id, 200)
        cls.client.wait_for_image_status(cls.image2_id, 'ACTIVE')
        resp, cls.image2 = cls.client.get_image(cls.image2_id)

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_image(cls.image1_id)
        cls.client.delete_image(cls.image2_id)
        cls.client.delete_image(cls.image3_id)
        cls.servers_client.delete_server(cls.server1['id'])
        cls.servers_client.delete_server(cls.server2['id'])
        super(ListImageFiltersTest, cls).tearDownClass()

    @attr(type='negative')
    def test_get_image_not_existing(self):
        # Check raises a NotFound
        self.assertRaises(exceptions.NotFound, self.client.get_image,
                          "nonexistingimageid")

    @attr(type='positive')
    def test_list_images_filter_by_status(self):
        # The list of images should contain only images with the
        # provided status
        params = {'status': 'ACTIVE'}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='positive')
    def test_list_images_filter_by_name(self):
        # List of all images should contain the expected images filtered
        # by name
        params = {'name': self.image1['name']}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='positive')
    def test_list_images_filter_by_server_id(self):
        # The images should contain images filtered by server id
        params = {'server': self.server1['id']}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]),
                        "Failed to find image %s in images. Got images %s" %
                        (self.image1_id, images))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='positive')
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

    @attr(type='positive')
    def test_list_images_filter_by_type(self):
        # The list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        resp, images = self.client.list_images(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image_ref]))

    @attr(type='positive')
    def test_list_images_limit_results(self):
        # Verify only the expected number of results are returned
        params = {'limit': '1'}
        resp, images = self.client.list_images(params)
        self.assertEqual(1, len(images))

    @attr(type='positive')
    def test_list_images_filter_by_changes_since(self):
        # Verify only updated images are returned in the detailed list

        #Becoming ACTIVE will modify the updated time
        #Filter by the image's created time
        params = {'changes-since': self.image3['created']}
        resp, images = self.client.list_images(params)
        found = any([i for i in images if i['id'] == self.image3_id])
        self.assertTrue(found)

    @attr(type='positive')
    def test_list_images_with_detail_filter_by_status(self):
        # Detailed list of all images should only contain images
        # with the provided status
        params = {'status': 'ACTIVE'}
        resp, images = self.client.list_images_with_detail(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='positive')
    def test_list_images_with_detail_filter_by_name(self):
        # Detailed list of all images should contain the expected
        # images filtered by name
        params = {'name': self.image1['name']}
        resp, images = self.client.list_images_with_detail(params)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image2_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image3_id]))

    @attr(type='positive')
    def test_list_images_with_detail_limit_results(self):
        # Verify only the expected number of results (with full details)
        # are returned
        params = {'limit': '1'}
        resp, images = self.client.list_images_with_detail(params)
        self.assertEqual(1, len(images))

    @attr(type='positive')
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

    @attr(type='positive')
    def test_list_images_with_detail_filter_by_type(self):
        # The detailed list of servers should be filtered by image type
        params = {'type': 'snapshot'}
        resp, images = self.client.list_images_with_detail(params)
        resp, image4 = self.client.get_image(self.image_ref)

        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image2_id]))
        self.assertTrue(any([i for i in images if i['id'] == self.image3_id]))
        self.assertFalse(any([i for i in images if i['id'] == self.image_ref]))

    @attr(type='positive')
    def test_list_images_with_detail_filter_by_changes_since(self):
        # Verify an update image is returned

        #Becoming ACTIVE will modify the updated time
        #Filter by the image's created time
        params = {'changes-since': self.image1['created']}
        resp, images = self.client.list_images_with_detail(params)
        self.assertTrue(any([i for i in images if i['id'] == self.image1_id]))

    @attr(type='negative')
    def test_get_nonexistant_image(self):
        # Negative test: GET on non existant image should fail
        try:
            resp, image = self.client.get_image(999)
        except Exception:
            pass
        else:
            self.fail('GET on non existant image should fail')
