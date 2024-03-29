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

from tempest.api.compute.keypairs import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class KeyPairsNegativeTestJSON(base.BaseKeypairTest):
    """Negative tests of keypairs API"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('29cca892-46ae-4d48-bc32-8fe7e731eb81')
    def test_keypair_create_with_invalid_pub_key(self):
        """Test keypair should not be created with a non RSA public key"""
        pub_key = "ssh-rsa JUNK nova@ubuntu"
        self.assertRaises(lib_exc.BadRequest,
                          self.create_keypair, pub_key=pub_key)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7cc32e47-4c42-489d-9623-c5e2cb5a2fa5')
    def test_keypair_delete_nonexistent_key(self):
        """Test non-existent key deletion should throw a proper error"""
        k_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name="keypair-non-existent")
        self.assertRaises(lib_exc.NotFound,
                          self.keypairs_client.delete_keypair,
                          k_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('dade320e-69ca-42a9-ba4a-345300f127e0')
    def test_create_keypair_with_empty_public_key(self):
        """Test keypair should not be created with an empty public key"""
        pub_key = ' '
        self.assertRaises(lib_exc.BadRequest, self.create_keypair,
                          pub_key=pub_key)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('fc100c19-2926-4b9c-8fdc-d0589ee2f9ff')
    def test_create_keypair_when_public_key_bits_exceeds_maximum(self):
        """Test keypair should not be created when public key are too long"""
        pub_key = 'ssh-rsa ' + 'A' * 2048 + ' openstack@ubuntu'
        self.assertRaises(lib_exc.BadRequest, self.create_keypair,
                          pub_key=pub_key)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0359a7f1-f002-4682-8073-0c91e4011b7c')
    def test_create_keypair_with_duplicate_name(self):
        """Test keypairs with duplicate names should not be created"""
        k_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='keypair')
        self.keypairs_client.create_keypair(name=k_name)
        # Now try the same keyname to create another key
        self.assertRaises(lib_exc.Conflict, self.create_keypair,
                          k_name)
        self.keypairs_client.delete_keypair(k_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1398abe1-4a84-45fb-9294-89f514daff00')
    def test_create_keypair_with_empty_name_string(self):
        """Test keypairs with empty name should not be created"""
        self.assertRaises(lib_exc.BadRequest, self.create_keypair,
                          '')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3faa916f-779f-4103-aca7-dc3538eee1b7')
    def test_create_keypair_with_long_keynames(self):
        """Test keypairs with name longer than 255 should not be created"""
        k_name = 'keypair-'.ljust(260, '0')
        self.assertRaises(lib_exc.BadRequest, self.create_keypair,
                          k_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('45fbe5e0-acb5-49aa-837a-ff8d0719db91')
    def test_create_keypair_invalid_name(self):
        """Test keypairs with an invalid name should not be created"""
        k_name = r'key_/.\@:'
        self.assertRaises(lib_exc.BadRequest, self.create_keypair,
                          k_name)
