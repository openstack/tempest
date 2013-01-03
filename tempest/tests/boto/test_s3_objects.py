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

from contextlib import closing

from boto.s3.key import Key
from nose.plugins.attrib import attr
import unittest2 as unittest

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest.testboto import BotoTestCase
from tempest.tests import boto


@attr("S3")
class S3BucketsTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(S3BucketsTest, cls).setUpClass()
        cls.os = clients.Manager()
        cls.client = cls.os.s3_client
        cls.config = cls.os.config

    @unittest.skip("Skipped until the Bug #1076534 is resolved")
    @attr(type='smoke')
    def test_create_get_delete_object(self):
        # S3 Create, get and delete object
        bucket_name = rand_name("s3bucket-")
        object_name = rand_name("s3object-")
        content = 'x' * 42
        bucket = self.client.create_bucket(bucket_name)
        self.addResourceCleanUp(self.destroy_bucket,
                                self.client.connection_data,
                                bucket_name)

        self.assertTrue(bucket.name == bucket_name)
        with closing(Key(bucket)) as key:
            key.key = object_name
            key.set_contents_from_string(content)
            readback = key.get_contents_as_string()
            self.assertTrue(readback == content)
            bucket.delete_key(key)
            self.assertBotoError(self.s3_error_code.client.NoSuchKey,
                                 key.get_contents_as_string)
