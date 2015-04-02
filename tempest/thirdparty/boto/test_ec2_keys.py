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


def compare_key_pairs(a, b):
    return (a.name == b.name and
            a.fingerprint == b.fingerprint)


class EC2KeysTest(boto_test.BotoTestCase):

    @classmethod
    def setup_clients(cls):
        super(EC2KeysTest, cls).setup_clients()
        cls.client = cls.os.ec2api_client

    @classmethod
    def resource_setup(cls):
        super(EC2KeysTest, cls).resource_setup()
        cls.ec = cls.ec2_error_code

# TODO(afazekas): merge create, delete, get test cases
    @test.idempotent_id('54236804-01b7-4cfe-a6f9-bce1340feec8')
    def test_create_ec2_keypair(self):
        # EC2 create KeyPair
        key_name = data_utils.rand_name("keypair")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))

    @test.idempotent_id('3283b898-f90c-4952-b238-3e42b8c3f34f')
    def test_delete_ec2_keypair(self):
        # EC2 delete KeyPair
        key_name = data_utils.rand_name("keypair")
        self.client.create_key_pair(key_name)
        self.client.delete_key_pair(key_name)
        self.assertIsNone(self.client.get_key_pair(key_name))

    @test.idempotent_id('fd89bd26-4d4d-4cf3-a303-65dd9158fcdc')
    def test_get_ec2_keypair(self):
        # EC2 get KeyPair
        key_name = data_utils.rand_name("keypair")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))

    @test.idempotent_id('daa73da1-e11c-4558-8d76-a716be79a401')
    def test_duplicate_ec2_keypair(self):
        # EC2 duplicate KeyPair
        key_name = data_utils.rand_name("keypair")
        self.addResourceCleanUp(self.client.delete_key_pair, key_name)
        keypair = self.client.create_key_pair(key_name)
        self.assertBotoError(self.ec.client.InvalidKeyPair.Duplicate,
                             self.client.create_key_pair,
                             key_name)
        self.assertTrue(compare_key_pairs(keypair,
                        self.client.get_key_pair(key_name)))
