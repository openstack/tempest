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

from tempest_lib.common.utils import data_utils

from tempest import test
from tempest.thirdparty.boto import test as boto_test


class S3BucketsTest(boto_test.BotoTestCase):

    @classmethod
    def setup_clients(cls):
        super(S3BucketsTest, cls).setup_clients()
        cls.client = cls.os.s3_client

    @test.idempotent_id('4678525d-8da0-4518-81c1-f1f67d595b00')
    def test_create_and_get_delete_bucket(self):
        # S3 Create, get and delete bucket
        bucket_name = data_utils.rand_name("s3bucket")
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
