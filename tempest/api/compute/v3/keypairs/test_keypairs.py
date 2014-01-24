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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import test


class KeyPairsV3TestJSON(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(KeyPairsV3TestJSON, cls).setUpClass()
        cls.client = cls.keypairs_client

    def _delete_keypair(self, keypair_name):
        resp, _ = self.client.delete_keypair(keypair_name)
        self.assertEqual(204, resp.status)

    def _create_keypair(self, keypair_name, pub_key=None):
        resp, body = self.client.create_keypair(keypair_name, pub_key)
        self.addCleanup(self._delete_keypair, keypair_name)
        return resp, body

    @test.attr(type='gate')
    def test_keypairs_create_list_delete(self):
        # Keypairs created should be available in the response list
        # Create 3 keypairs
        key_list = list()
        for i in range(3):
            k_name = data_utils.rand_name('keypair-')
            resp, keypair = self._create_keypair(k_name)
            # Need to pop these keys so that our compare doesn't fail later,
            # as the keypair dicts from list API doesn't have them.
            keypair.pop('private_key')
            keypair.pop('user_id')
            self.assertEqual(201, resp.status)
            key_list.append(keypair)
        # Fetch all keypairs and verify the list
        # has all created keypairs
        resp, fetched_list = self.client.list_keypairs()
        self.assertEqual(200, resp.status)
        # We need to remove the extra 'keypair' element in the
        # returned dict. See comment in keypairs_client.list_keypairs()
        new_list = list()
        for keypair in fetched_list:
            new_list.append(keypair['keypair'])
        fetched_list = new_list
        # Now check if all the created keypairs are in the fetched list
        missing_kps = [kp for kp in key_list if kp not in fetched_list]
        self.assertFalse(missing_kps,
                         "Failed to find keypairs %s in fetched list"
                         % ', '.join(m_key['name'] for m_key in missing_kps))

    @test.attr(type='gate')
    def test_keypair_create_delete(self):
        # Keypair should be created, verified and deleted
        k_name = data_utils.rand_name('keypair-')
        resp, keypair = self._create_keypair(k_name)
        self.assertEqual(201, resp.status)
        private_key = keypair['private_key']
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name")
        self.assertTrue(private_key is not None,
                        "Field private_key is empty or not found.")

    @test.attr(type='gate')
    def test_get_keypair_detail(self):
        # Keypair should be created, Got details by name and deleted
        k_name = data_utils.rand_name('keypair-')
        resp, keypair = self._create_keypair(k_name)
        resp, keypair_detail = self.client.get_keypair(k_name)
        self.assertEqual(200, resp.status)
        self.assertIn('name', keypair_detail)
        self.assertIn('public_key', keypair_detail)
        self.assertEqual(keypair_detail['name'], k_name,
                         "The created keypair name is not equal "
                         "to requested name")
        public_key = keypair_detail['public_key']
        self.assertTrue(public_key is not None,
                        "Field public_key is empty or not found.")

    @test.attr(type='gate')
    def test_keypair_create_with_pub_key(self):
        # Keypair should be created with a given public key
        k_name = data_utils.rand_name('keypair-')
        pub_key = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCs"
                   "Ne3/1ILNCqFyfYWDeTKLD6jEXC2OQHLmietMWW+/vd"
                   "aZq7KZEwO0jhglaFjU1mpqq4Gz5RX156sCTNM9vRbw"
                   "KAxfsdF9laBYVsex3m3Wmui3uYrKyumsoJn2g9GNnG1P"
                   "I1mrVjZ61i0GY3khna+wzlTpCCmy5HNlrmbj3XLqBUpip"
                   "TOXmsnr4sChzC53KCd8LXuwc1i/CZPvF+3XipvAgFSE53pCt"
                   "LOeB1kYMOBaiUPLQTWXR3JpckqFIQwhIH0zoHlJvZE8hh90"
                   "XcPojYN56tI0OlrGqojbediJYD0rUsJu4weZpbn8vilb3JuDY+jws"
                   "snSA8wzBx3A/8y9Pp1B nova@ubuntu")
        resp, keypair = self._create_keypair(k_name, pub_key)
        self.assertEqual(201, resp.status)
        self.assertFalse('private_key' in keypair,
                         "Field private_key is not empty!")
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name!")
