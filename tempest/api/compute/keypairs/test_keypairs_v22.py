# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.api.compute.keypairs import test_keypairs
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class KeyPairsV22TestJSON(test_keypairs.KeyPairsV2TestJSON):
    min_microversion = '2.2'
    max_microversion = 'latest'

    def _check_keypair_type(self, keypair, keypair_type):
        if keypair_type is None:
            keypair_type = 'ssh'
        self.assertEqual(keypair_type, keypair['type'])

    def _test_keypairs_create_list_show(self, keypair_type=None):
        k_name = data_utils.rand_name('keypair')
        keypair = self.create_keypair(k_name, keypair_type=keypair_type)
        # Verify whether 'type' is present in keypair create response of
        # version 2.2 and it is with default value 'ssh'.
        self._check_keypair_type(keypair, keypair_type)
        keypair_detail = self.keypairs_client.show_keypair(k_name)['keypair']
        self._check_keypair_type(keypair_detail, keypair_type)
        fetched_list = self.keypairs_client.list_keypairs()['keypairs']
        for keypair in fetched_list:
            # Verify whether 'type' is present in keypair list response of
            # version 2.2 and it is with default value 'ssh'.
            if keypair['keypair']['name'] == k_name:
                self._check_keypair_type(keypair['keypair'], keypair_type)

    @decorators.idempotent_id('8726fa85-7f98-4b20-af9e-f710a4f3391c')
    def test_keypairsv22_create_list_show(self):
        self._test_keypairs_create_list_show()

    @decorators.idempotent_id('89d59d43-f735-441a-abcf-0601727f47b6')
    def test_keypairsv22_create_list_show_with_type(self):
        keypair_type = 'x509'
        self._test_keypairs_create_list_show(keypair_type=keypair_type)
