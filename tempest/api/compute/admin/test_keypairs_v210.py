# Copyright 2016 NEC Corporation.
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


class KeyPairsV210TestJSON(base.BaseKeypairTest):
    credentials = ['primary', 'admin']
    min_microversion = '2.10'

    @classmethod
    def setup_clients(cls):
        super(KeyPairsV210TestJSON, cls).setup_clients()
        cls.client = cls.os_admin.keypairs_client
        cls.non_admin_client = cls.os_primary.keypairs_client

    def _create_and_check_keypairs(self, user_id):
        key_list = list()
        for _ in range(2):
            k_name = data_utils.rand_name('keypair')
            keypair = self.create_keypair(k_name,
                                          keypair_type='ssh',
                                          user_id=user_id,
                                          client=self.client)
            self.assertEqual(k_name, keypair['name'],
                             "The created keypair name is not equal "
                             "to the requested name!")
            self.assertEqual(user_id, keypair['user_id'],
                             "The created keypair is not for requested user!")
            keypair.pop('private_key', None)
            keypair.pop('user_id')
            key_list.append(keypair)
        return key_list

    @decorators.idempotent_id('3c8484af-cfb3-48f6-b8ba-d5d58bbf3eac')
    def test_admin_manage_keypairs_for_other_users(self):
        user_id = self.non_admin_client.user_id
        key_list = self._create_and_check_keypairs(user_id)
        first_keyname = key_list[0]['name']
        keypair_detail = self.client.show_keypair(first_keyname,
                                                  user_id=user_id)['keypair']
        self.assertEqual(first_keyname, keypair_detail['name'])
        self.assertEqual(user_id, keypair_detail['user_id'],
                         "The fetched keypair is not for requested user!")
        # Create a admin keypair
        admin_keypair = self.create_keypair(keypair_type='ssh',
                                            client=self.client)
        admin_keypair.pop('private_key', None)
        admin_keypair.pop('user_id')

        # Admin fetch keypairs list of non admin user
        keypairs = self.client.list_keypairs(user_id=user_id)['keypairs']
        fetched_list = [keypair['keypair'] for keypair in keypairs]

        # Check admin keypair is not present in non admin user keypairs list
        self.assertNotIn(admin_keypair, fetched_list,
                         "The fetched user keypairs has admin keypair!")

        # Now check if all the created keypairs are in the fetched list
        missing_kps = [kp for kp in key_list if kp not in fetched_list]
        self.assertFalse(missing_kps,
                         "Failed to find keypairs %s in fetched list"
                         % ', '.join(m_key['name'] for m_key in missing_kps))
