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

import os

import testtools

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.thirdparty.boto.test import BotoTestCase
from tempest.thirdparty.boto.utils.s3 import s3_upload_dir
from tempest.thirdparty.boto.utils.wait import state_wait


class S3ImagesTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(S3ImagesTest, cls).setUpClass()
        if not cls.conclusion['A_I_IMAGES_READY']:
            raise cls.skipException("".join(("EC2 ", cls.__name__,
                                    ": requires ami/aki/ari manifest")))
        cls.os = clients.Manager()
        cls.s3_client = cls.os.s3_client
        cls.images_client = cls.os.ec2api_client
        config = cls.config
        cls.materials_path = config.boto.s3_materials_path
        cls.ami_manifest = config.boto.ami_manifest
        cls.aki_manifest = config.boto.aki_manifest
        cls.ari_manifest = config.boto.ari_manifest
        cls.ami_path = cls.materials_path + os.sep + cls.ami_manifest
        cls.aki_path = cls.materials_path + os.sep + cls.aki_manifest
        cls.ari_path = cls.materials_path + os.sep + cls.ari_manifest
        cls.bucket_name = rand_name("bucket-")
        bucket = cls.s3_client.create_bucket(cls.bucket_name)
        cls.addResourceCleanUp(cls.destroy_bucket,
                               cls.s3_client.connection_data,
                               cls.bucket_name)
        s3_upload_dir(bucket, cls.materials_path)

    #Note(afazekas): Without the normal status change test!
    # otherwise I would skip it too
    @attr(type='smoke')
    def test_register_get_deregister_ami_image(self):
        # Register and deregister ami image
        image = {"name": rand_name("ami-name-"),
                 "location": self.bucket_name + "/" + self.ami_manifest,
                 "type": "ami"}
        image["image_id"] = self.images_client.register_image(
            name=image["name"],
            image_location=image["location"])
        #Note(afazekas): delete_snapshot=True might trigger boto lib? bug
        image["cleanUp"] = self.addResourceCleanUp(
            self.images_client.deregister_image,
            image["image_id"])
        self.assertEqual(image["image_id"][0:3], image["type"])
        retrieved_image = self.images_client.get_image(image["image_id"])
        self.assertTrue(retrieved_image.name == image["name"])
        self.assertTrue(retrieved_image.id == image["image_id"])
        state = retrieved_image.state
        if state != "available":
            def _state():
                retr = self.images_client.get_image(image["image_id"])
                return retr.state
            state = state_wait(_state, "available")
        self.assertEqual("available", state)
        self.images_client.deregister_image(image["image_id"])
        self.assertNotIn(image["image_id"], str(
            self.images_client.get_all_images()))
        self.cancelResourceCleanUp(image["cleanUp"])

    def test_register_get_deregister_aki_image(self):
        # Register and deregister aki image
        image = {"name": rand_name("aki-name-"),
                 "location": self.bucket_name + "/" + self.aki_manifest,
                 "type": "aki"}
        image["image_id"] = self.images_client.register_image(
            name=image["name"],
            image_location=image["location"])
        image["cleanUp"] = self.addResourceCleanUp(
            self.images_client.deregister_image,
            image["image_id"])
        self.assertEqual(image["image_id"][0:3], image["type"])
        retrieved_image = self.images_client.get_image(image["image_id"])
        self.assertTrue(retrieved_image.name == image["name"])
        self.assertTrue(retrieved_image.id == image["image_id"])
        self.assertIn(retrieved_image.state, self.valid_image_state)
        if retrieved_image.state != "available":
            self.assertImageStateWait(retrieved_image, "available")
        self.images_client.deregister_image(image["image_id"])
        self.assertNotIn(image["image_id"], str(
            self.images_client.get_all_images()))
        self.cancelResourceCleanUp(image["cleanUp"])

    @testtools.skip("Skipped until the Bug #1074908 and #1074904 is resolved")
    def test_register_get_deregister_ari_image(self):
        # Register and deregister ari image
        image = {"name": rand_name("ari-name-"),
                 "location": "/" + self.bucket_name + "/" + self.ari_manifest,
                 "type": "ari"}
        image["image_id"] = self.images_client.register_image(
            name=image["name"],
            image_location=image["location"])
        image["cleanUp"] = self.addResourceCleanUp(
            self.images_client.deregister_image,
            image["image_id"])
        self.assertEqual(image["image_id"][0:3], image["type"])
        retrieved_image = self.images_client.get_image(image["image_id"])
        self.assertIn(retrieved_image.state, self.valid_image_state)
        if retrieved_image.state != "available":
            self.assertImageStateWait(retrieved_image, "available")
        self.assertIn(retrieved_image.state, self.valid_image_state)
        self.assertTrue(retrieved_image.name == image["name"])
        self.assertTrue(retrieved_image.id == image["image_id"])
        self.images_client.deregister_image(image["image_id"])
        self.cancelResourceCleanUp(image["cleanUp"])

#TODO(afazekas): less copy-paste style
