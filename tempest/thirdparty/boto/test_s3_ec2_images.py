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

import os

from tempest_lib.common.utils import data_utils

from tempest import config
from tempest import test
from tempest.thirdparty.boto import test as boto_test
from tempest.thirdparty.boto.utils import s3

CONF = config.CONF


class S3ImagesTest(boto_test.BotoTestCase):

    @classmethod
    def setup_clients(cls):
        super(S3ImagesTest, cls).setup_clients()
        cls.s3_client = cls.os.s3_client
        cls.images_client = cls.os.ec2api_client

    @classmethod
    def resource_setup(cls):
        super(S3ImagesTest, cls).resource_setup()
        if not cls.conclusion['A_I_IMAGES_READY']:
            raise cls.skipException("".join(("EC2 ", cls.__name__,
                                    ": requires ami/aki/ari manifest")))
        cls.materials_path = CONF.boto.s3_materials_path
        cls.ami_manifest = CONF.boto.ami_manifest
        cls.aki_manifest = CONF.boto.aki_manifest
        cls.ari_manifest = CONF.boto.ari_manifest
        cls.ami_path = cls.materials_path + os.sep + cls.ami_manifest
        cls.aki_path = cls.materials_path + os.sep + cls.aki_manifest
        cls.ari_path = cls.materials_path + os.sep + cls.ari_manifest
        cls.bucket_name = data_utils.rand_name("bucket")
        bucket = cls.s3_client.create_bucket(cls.bucket_name)
        cls.addResourceCleanUp(cls.destroy_bucket,
                               cls.s3_client.connection_data,
                               cls.bucket_name)
        s3.s3_upload_dir(bucket, cls.materials_path)

    @test.idempotent_id('f9d360a5-0188-4c77-9db2-4c34c28d12a5')
    def test_register_get_deregister_ami_image(self):
        # Register and deregister ami image
        image = {"name": data_utils.rand_name("ami-name"),
                 "location": self.bucket_name + "/" + self.ami_manifest,
                 "type": "ami"}
        image["image_id"] = self.images_client.register_image(
            name=image["name"],
            image_location=image["location"])
        # NOTE(afazekas): delete_snapshot=True might trigger boto lib? bug
        image["cleanUp"] = self.addResourceCleanUp(
            self.images_client.deregister_image,
            image["image_id"])
        self.assertEqual(image["image_id"][0:3], image["type"])
        retrieved_image = self.images_client.get_image(image["image_id"])
        self.assertTrue(retrieved_image.name == image["name"])
        self.assertTrue(retrieved_image.id == image["image_id"])
        if retrieved_image.state != "available":
            self.assertImageStateWait(retrieved_image, "available")
        self.images_client.deregister_image(image["image_id"])
        self.assertNotIn(image["image_id"], str(
            self.images_client.get_all_images()))
        self.cancelResourceCleanUp(image["cleanUp"])

    @test.idempotent_id('42cca5b0-453b-4618-b99f-dbc039db426f')
    def test_register_get_deregister_aki_image(self):
        # Register and deregister aki image
        image = {"name": data_utils.rand_name("aki-name"),
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

    @test.idempotent_id('1359e860-841c-43bb-80f3-bb389cbfd81d')
    def test_register_get_deregister_ari_image(self):
        # Register and deregister ari image
        image = {"name": data_utils.rand_name("ari-name"),
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

# TODO(afazekas): less copy-paste style
