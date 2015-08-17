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
import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import keypairs_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestKeyPairsClient(base.TestCase):

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
        body = '{"keypairs": []}'
        if bytes_body:
            body = body.encode('utf-8')
        expected = {"keypairs": []}
        response = (httplib2.Response({'status': 200}), body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=response))
        self.assertEqual(expected, self.client.list_keypairs())

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
        serialized_body = json.dumps(fake_keypair)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_keypair("test")
        self.assertEqual(fake_keypair, resp)

    def test_show_keypair_with_str_body(self):
        self._test_show_keypair()

    def test_show_keypair_with_bytes_body(self):
        self._test_show_keypair(bytes_body=True)

    def _test_create_keypair(self, bytes_body=False):
        fake_keypair = copy.deepcopy(self.FAKE_KEYPAIR)
        fake_keypair["keypair"].update({"private_key": "foo"})
        serialized_body = json.dumps(fake_keypair)
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.post',
            return_value=mocked_resp))
        resp = self.client.create_keypair(name='test')
        self.assertEqual(fake_keypair, resp)

    def test_create_keypair_with_str_body(self):
        self._test_create_keypair()

    def test_create_keypair_with_bytes_body(self):
        self._test_create_keypair(bytes_body=True)

    def test_delete_keypair(self):
        expected = {}
        mocked_resp = (httplib2.Response({'status': 202}), None)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.delete',
            return_value=mocked_resp))
        resp = self.client.delete_keypair('test')
        self.assertEqual(expected, resp)
