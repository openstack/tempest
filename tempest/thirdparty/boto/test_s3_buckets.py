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

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.test import skip_because
from tempest.thirdparty.boto.test import BotoTestCase


class S3BucketsTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(S3BucketsTest, cls).setUpClass()
        cls.os = clients.Manager()
        cls.client = cls.os.s3_client

    @skip_because(bug="1076965")
    @attr(type='smoke')
    def test_create_and_get_delete_bucket(self):
        # S3 Create, get and delete bucket
        bucket_name = rand_name("s3bucket-")
        cleanup_key = self.addResourceCleanUp(self.client.delete_bucket,
                                              bucket_name)
        bucket = self.client.create_bucket(bucket_name)
        self.assertTrue(bucket.name == bucket_name)
        bucket = self.client.get_bucket(bucket_name)
        self.assertTrue(bucket.name == bucket_name)
        self.client.delete_bucket(bucket_name)
        self.assertBotoError(self.s3_error_code.client.NoSuchBucket,
                             self.client.get_bucket, bucket_name)
        self.cancelResourceCleanUp(cleanup_key)
