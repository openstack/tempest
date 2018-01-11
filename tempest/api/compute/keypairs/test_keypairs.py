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

from tempest.api.compute.keypairs import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class KeyPairsV2TestJSON(base.BaseKeypairTest):
    max_microversion = '2.1'

    @decorators.idempotent_id('1d1dbedb-d7a0-432a-9d09-83f543c3c19b')
    def test_keypairs_create_list_delete(self):
        # Keypairs created should be available in the response list
        # Create 3 keypairs
        key_list = list()
        for _ in range(3):
            keypair = self.create_keypair()
            # Need to pop these keys so that our compare doesn't fail later,
            # as the keypair dicts from list API doesn't have them.
            keypair.pop('private_key')
            keypair.pop('user_id')
            key_list.append(keypair)
        # Fetch all keypairs and verify the list
        # has all created keypairs
        fetched_list = self.keypairs_client.list_keypairs()['keypairs']
        new_list = list()
        for keypair in fetched_list:
            new_list.append(keypair['keypair'])
        fetched_list = new_list
        # Now check if all the created keypairs are in the fetched list
        missing_kps = [kp for kp in key_list if kp not in fetched_list]
        self.assertFalse(missing_kps,
                         "Failed to find keypairs %s in fetched list"
                         % ', '.join(m_key['name'] for m_key in missing_kps))

    @decorators.idempotent_id('6c1d3123-4519-4742-9194-622cb1714b7d')
    def test_keypair_create_delete(self):
        # Keypair should be created, verified and deleted
        k_name = data_utils.rand_name('keypair')
        keypair = self.create_keypair(k_name)
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name")

    @decorators.idempotent_id('a4233d5d-52d8-47cc-9a25-e1864527e3df')
    def test_get_keypair_detail(self):
        # Keypair should be created, Got details by name and deleted
        k_name = data_utils.rand_name('keypair')
        self.create_keypair(k_name)
        keypair_detail = self.keypairs_client.show_keypair(k_name)['keypair']
        self.assertEqual(keypair_detail['name'], k_name,
                         "The created keypair name is not equal "
                         "to requested name")

    @decorators.idempotent_id('39c90c6a-304a-49dd-95ec-2366129def05')
    def test_keypair_create_with_pub_key(self):
        # Keypair should be created with a given public key
        k_name = data_utils.rand_name('keypair')
        pub_key = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCs"
                   "Ne3/1ILNCqFyfYWDeTKLD6jEXC2OQHLmietMWW+/vd"
                   "aZq7KZEwO0jhglaFjU1mpqq4Gz5RX156sCTNM9vRbw"
                   "KAxfsdF9laBYVsex3m3Wmui3uYrKyumsoJn2g9GNnG1P"
                   "I1mrVjZ61i0GY3khna+wzlTpCCmy5HNlrmbj3XLqBUpip"
                   "TOXmsnr4sChzC53KCd8LXuwc1i/CZPvF+3XipvAgFSE53pCt"
                   "LOeB1kYMOBaiUPLQTWXR3JpckqFIQwhIH0zoHlJvZE8hh90"
                   "XcPojYN56tI0OlrGqojbediJYD0rUsJu4weZpbn8vilb3JuDY+jws"
                   "snSA8wzBx3A/8y9Pp1B nova@ubuntu")
        keypair = self.create_keypair(k_name, pub_key)
        self.assertNotIn('private_key', keypair,
                         "Field private_key is not empty!")
        key_name = keypair['name']
        self.assertEqual(key_name, k_name,
                         "The created keypair name is not equal "
                         "to the requested name!")
