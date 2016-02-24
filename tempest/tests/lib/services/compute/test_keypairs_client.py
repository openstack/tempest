# Copyright 2015 NEC Corporation.  All rights reserved.
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

import copy

from tempest.lib.services.compute import keypairs_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestKeyPairsClient(base.BaseComputeServiceTest):

    FAKE_KEYPAIR = {"keypair": {
        "public_key": "ssh-rsa foo Generated-by-Nova",
        "name": u'\u2740(*\xb4\u25e1`*)\u2740',
        "user_id": "525d55f98980415ba98e634972fa4a10",
        "fingerprint": "76:24:66:49:d7:ca:6e:5c:77:ea:8e:bb:9c:15:5f:98"
        }}

    def setUp(self):
        super(TestKeyPairsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = keypairs_client.KeyPairsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_keypairs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_keypairs,
            'tempest.lib.common.rest_client.RestClient.get',
            {"keypairs": []},
            bytes_body)

    def test_list_keypairs_with_str_body(self):
        self._test_list_keypairs()

    def test_list_keypairs_with_bytes_body(self):
        self._test_list_keypairs(bytes_body=True)

    def _test_show_keypair(self, bytes_body=False):
        fake_keypair = copy.deepcopy(self.FAKE_KEYPAIR)
        fake_keypair["keypair"].update({
            "deleted": False,
            "created_at": "2015-07-22T04:53:52.000000",
            "updated_at": None,
            "deleted_at": None,
            "id": 1
            })

        self.check_service_client_function(
            self.client.show_keypair,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_keypair,
            bytes_body,
            keypair_name="test")

    def test_show_keypair_with_str_body(self):
        self._test_show_keypair()

    def test_show_keypair_with_bytes_body(self):
        self._test_show_keypair(bytes_body=True)

    def _test_create_keypair(self, bytes_body=False):
        fake_keypair = copy.deepcopy(self.FAKE_KEYPAIR)
        fake_keypair["keypair"].update({"private_key": "foo"})

        self.check_service_client_function(
            self.client.create_keypair,
            'tempest.lib.common.rest_client.RestClient.post',
            fake_keypair,
            bytes_body,
            name="test")

    def test_create_keypair_with_str_body(self):
        self._test_create_keypair()

    def test_create_keypair_with_bytes_body(self):
        self._test_create_keypair(bytes_body=True)

    def test_delete_keypair(self):
        self.check_service_client_function(
            self.client.delete_keypair,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, keypair_name='test')
