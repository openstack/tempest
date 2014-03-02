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

from tempest.common.utils import data_utils
from tempest import test
from tempest.thirdparty.boto import test as boto_test


def compare_key_pairs(a, b):
    return (a.name == b.name and
            a.fingerprint == b.fingerprint)


class EC2KeysTest(boto_test.BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(EC2KeysTest, cls).setUpClass()
        cls.client = cls.os.ec2api_client
        cls.ec = cls.ec2_error_code

# TODO(afazekas): merge create, delete, get test cases
    @test.attr(type='smoke')
    def test_create_ec2_keypair(self):
        # EC2 create KeyPair
        key_name = data_utils.rand_name("keypair-")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))

    @test.skip_because(bug="1072318")
    @test.attr(type='smoke')
    def test_delete_ec2_keypair(self):
        # EC2 delete KeyPair
        key_name = data_utils.rand_name("keypair-")
        self.client.create_key_pair(key_name)
        self.client.delete_key_pair(key_name)
        self.assertIsNone(self.client.get_key_pair(key_name))

    @test.attr(type='smoke')
    def test_get_ec2_keypair(self):
        # EC2 get KeyPair
        key_name = data_utils.rand_name("keypair-")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))

    @test.attr(type='smoke')
    def test_duplicate_ec2_keypair(self):
        # EC2 duplicate KeyPair
        key_name = data_utils.rand_name("keypair-")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertBotoError(self.ec.client.InvalidKeyPair.Duplicate,
                             self.client.create_key_pair,
                             key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))
