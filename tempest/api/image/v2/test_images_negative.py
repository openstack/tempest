# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
# Copyright 2013 IBM Corp.
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

import uuid

from tempest.api.image import base
from tempest import exceptions
from tempest.test import attr


class ImagesNegativeTest(base.BaseV2ImageTest):

    """
    here we have -ve tests for get_image and delete_image api

    Tests
        ** get non-existent image
        ** get image with image_id=NULL
        ** get the deleted image
        ** delete non-existent image
        ** delete rimage with  image_id=NULL
        ** delete the deleted image
     """

    @attr(type=['negative', 'gate'])
    def test_get_non_existent_image(self):
        # get the non-existent image
        non_existent_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.get_image,
                          non_existent_id)

    @attr(type=['negative', 'gate'])
    def test_get_image_null_id(self):
        # get image with image_id = NULL
        image_id = ""
        self.assertRaises(exceptions.NotFound, self.client.get_image, image_id)

    @attr(type=['negative', 'gate'])
    def test_get_delete_deleted_image(self):
        # get and delete the deleted image
        # create and delete image
        resp, body = self.client.create_image(name='test',
                                              container_format='bare',
                                              disk_format='raw')
        image_id = body['id']
        self.assertEqual(201, resp.status)
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

        # get the deleted image
        self.assertRaises(exceptions.NotFound, self.client.get_image, image_id)

        # delete the deleted image
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          image_id)

    @attr(type=['negative', 'gate'])
    def test_delete_non_existing_image(self):
        # delete non-existent image
        non_existent_image_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @attr(type=['negative', 'gate'])
    def test_delete_image_null_id(self):
        # delete image with image_id=NULL
        image_id = ""
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          image_id)
