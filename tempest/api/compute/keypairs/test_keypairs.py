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

from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class KeyPairsTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(KeyPairsTestJSON, cls).setUpClass()
        cls.client = cls.keypairs_client

    @attr(type='positive')
    def test_keypairs_create_list_delete(self):
        # Keypairs created should be available in the response list
        #Create 3 keypairs
        key_list = list()
        for i in range(3):
            k_name = rand_name('keypair-')
            resp, keypair = self.client.create_keypair(k_name)
            #Need to pop these keys so that our compare doesn't fail later,
            #as the keypair dicts from list API doesn't have them.
            keypair.pop('private_key')
            keypair.pop('user_id')
            self.assertEqual(200, resp.status)
            key_list.append(keypair)
        #Fetch all keypairs and verify the list
        #has all created keypairs
        resp, fetched_list = self.client.list_keypairs()
        self.assertEqual(200, resp.status)
        #We need to remove the extra 'keypair' element in the
        #returned dict. See comment in keypairs_client.list_keypairs()
        new_list = list()
        for keypair in fetched_list:
            new_list.append(keypair['keypair'])
        fetched_list = new_list
        #Now check if all the created keypairs are in the fetched list
        missing_kps = [kp for kp in key_list if kp not in fetched_list]
        self.assertFalse(missing_kps,
                         "Failed to find keypairs %s in fetched list"
                         % ', '.join(m_key['name'] for m_key in missing_kps))
        #Delete all the keypairs created
        for keypair in key_list:
            resp, _ = self.client.delete_keypair(keypair['name'])
            self.assertEqual(202, resp.status)

    @attr(type='positive')
    def test_keypair_create_delete(self):
        # Keypair should be created, verified and deleted
        k_name = rand_name('keypair-')
        resp, keypair = self.client.create_keypair(k_name)
        self.assertEqual(200, resp.status)
        private_key = keypair['private_key']
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name")
        self.assertTrue(private_key is not None,
                        "Field private_key is empty or not found.")
        resp, _ = self.client.delete_keypair(k_name)
        self.assertEqual(202, resp.status)

    @attr(type='positive')
    def test_get_keypair_detail(self):
        # Keypair should be created, Got details by name and deleted
        k_name = rand_name('keypair-')
        resp, keypair = self.client.create_keypair(k_name)
        try:
            resp, keypair_detail = self.client.get_keypair(k_name)
            self.assertEqual(200, resp.status)
            self.assertTrue('name' in keypair_detail)
            self.assertTrue('public_key' in keypair_detail)
            self.assertEqual(keypair_detail['name'], k_name,
                             "The created keypair name is not equal "
                             "to requested name")
            public_key = keypair_detail['public_key']
            self.assertTrue(public_key is not None,
                            "Field public_key is empty or not found.")
        except Exception:
            self.fail("GET keypair details requested by keypair name "
                      "has failed")
        finally:
            resp, _ = self.client.delete_keypair(k_name)
            self.assertEqual(202, resp.status)

    @attr(type='positive')
    def test_keypair_create_with_pub_key(self):
        # Keypair should be created with a given public key
        k_name = rand_name('keypair-')
        pub_key = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCs"
                   "Ne3/1ILNCqFyfYWDeTKLD6jEXC2OQHLmietMWW+/vd"
                   "aZq7KZEwO0jhglaFjU1mpqq4Gz5RX156sCTNM9vRbw"
                   "KAxfsdF9laBYVsex3m3Wmui3uYrKyumsoJn2g9GNnG1P"
                   "I1mrVjZ61i0GY3khna+wzlTpCCmy5HNlrmbj3XLqBUpip"
                   "TOXmsnr4sChzC53KCd8LXuwc1i/CZPvF+3XipvAgFSE53pCt"
                   "LOeB1kYMOBaiUPLQTWXR3JpckqFIQwhIH0zoHlJvZE8hh90"
                   "XcPojYN56tI0OlrGqojbediJYD0rUsJu4weZpbn8vilb3JuDY+jws"
                   "snSA8wzBx3A/8y9Pp1B nova@ubuntu")
        resp, keypair = self.client.create_keypair(k_name, pub_key)
        self.assertEqual(200, resp.status)
        self.assertFalse('private_key' in keypair,
                         "Field private_key is not empty!")
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name!")
        resp, _ = self.client.delete_keypair(k_name)
        self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_keypair_create_with_invalid_pub_key(self):
        # Keypair should not be created with a non RSA public key
        k_name = rand_name('keypair-')
        pub_key = "ssh-rsa JUNK nova@ubuntu"
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_keypair, k_name, pub_key)

    @attr(type='negative')
    def test_keypair_delete_nonexistant_key(self):
        # Non-existant key deletion should throw a proper error
        k_name = rand_name("keypair-non-existant-")
        self.assertRaises(exceptions.NotFound, self.client.delete_keypair,
                          k_name)

    @attr(type='negative')
    def test_create_keypair_with_empty_public_key(self):
        # Keypair should not be created with an empty public key
        k_name = rand_name("keypair-")
        pub_key = ' '
        self.assertRaises(exceptions.BadRequest, self.client.create_keypair,
                          k_name, pub_key)

    @attr(type='negative')
    def test_create_keypair_when_public_key_bits_exceeds_maximum(self):
        # Keypair should not be created when public key bits are too long
        k_name = rand_name("keypair-")
        pub_key = 'ssh-rsa ' + 'A' * 2048 + ' openstack@ubuntu'
        self.assertRaises(exceptions.BadRequest, self.client.create_keypair,
                          k_name, pub_key)

    @attr(type='negative')
    def test_create_keypair_with_duplicate_name(self):
        # Keypairs with duplicate names should not be created
        k_name = rand_name('keypair-')
        resp, _ = self.client.create_keypair(k_name)
        self.assertEqual(200, resp.status)
        #Now try the same keyname to ceate another key
        self.assertRaises(exceptions.Duplicate, self.client.create_keypair,
                          k_name)
        resp, _ = self.client.delete_keypair(k_name)
        self.assertEqual(202, resp.status)

    @attr(type='negative')
    def test_create_keypair_with_empty_name_string(self):
        # Keypairs with name being an empty string should not be created
        self.assertRaises(exceptions.BadRequest, self.client.create_keypair,
                          '')

    @attr(type='negative')
    def test_create_keypair_with_long_keynames(self):
        # Keypairs with name longer than 255 chars should not be created
        k_name = 'keypair-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest, self.client.create_keypair,
                          k_name)

    @attr(type='negative')
    def test_create_keypair_invalid_name(self):
        # Keypairs with name being an invalid name should not be created
        k_name = 'key_/.\@:'
        self.assertRaises(exceptions.BadRequest, self.client.create_keypair,
                          k_name)


class KeyPairsTestXML(KeyPairsTestJSON):
    _interface = 'xml'
