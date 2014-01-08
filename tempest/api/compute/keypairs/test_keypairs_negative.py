# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp
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
from tempest import test


class KeyPairsNegativeTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(KeyPairsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.keypairs_client

    def _create_keypair(self, keypair_name, pub_key=None):
        self.client.create_keypair(keypair_name, pub_key)
        self.addCleanup(self.client.delete_keypair, keypair_name)

    @test.attr(type=['negative', 'gate'])
    def test_keypair_create_with_invalid_pub_key(self):
        # Keypair should not be created with a non RSA public key
        k_name = data_utils.rand_name('keypair-')
        pub_key = "ssh-rsa JUNK nova@ubuntu"
        self.assertRaises(exceptions.BadRequest,
                          self._create_keypair, k_name, pub_key)

    @test.attr(type=['negative', 'gate'])
    def test_keypair_delete_nonexistant_key(self):
        # Non-existant key deletion should throw a proper error
        k_name = data_utils.rand_name("keypair-non-existant-")
        self.assertRaises(exceptions.NotFound, self.client.delete_keypair,
                          k_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_with_empty_public_key(self):
        # Keypair should not be created with an empty public key
        k_name = data_utils.rand_name("keypair-")
        pub_key = ' '
        self.assertRaises(exceptions.BadRequest, self._create_keypair,
                          k_name, pub_key)

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_when_public_key_bits_exceeds_maximum(self):
        # Keypair should not be created when public key bits are too long
        k_name = data_utils.rand_name("keypair-")
        pub_key = 'ssh-rsa ' + 'A' * 2048 + ' openstack@ubuntu'
        self.assertRaises(exceptions.BadRequest, self._create_keypair,
                          k_name, pub_key)

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_with_duplicate_name(self):
        # Keypairs with duplicate names should not be created
        k_name = data_utils.rand_name('keypair-')
        resp, _ = self.client.create_keypair(k_name)
        self.assertEqual(200, resp.status)
        # Now try the same keyname to create another key
        self.assertRaises(exceptions.Conflict, self._create_keypair,
                          k_name)
        resp, _ = self.client.delete_keypair(k_name)
        self.assertEqual(202, resp.status)

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_with_empty_name_string(self):
        # Keypairs with name being an empty string should not be created
        self.assertRaises(exceptions.BadRequest, self._create_keypair,
                          '')

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_with_long_keynames(self):
        # Keypairs with name longer than 255 chars should not be created
        k_name = 'keypair-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest, self._create_keypair,
                          k_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_keypair_invalid_name(self):
        # Keypairs with name being an invalid name should not be created
        k_name = 'key_/.\@:'
        self.assertRaises(exceptions.BadRequest, self._create_keypair,
                          k_name)


class KeyPairsNegativeTestXML(KeyPairsNegativeTestJSON):
    _interface = 'xml'
