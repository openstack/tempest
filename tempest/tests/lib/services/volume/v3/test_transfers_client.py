# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

import copy
from unittest import mock

from oslo_serialization import jsonutils as json

from tempest.lib.services.volume.v3 import transfers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTransfersClient(base.BaseServiceTest):

    FAKE_VOLUME_TRANSFER_ID = "0e89cdd1-6249-421b-96d8-25fac0623d42"

    FAKE_VOLUME_TRANSFER_INFO = {
        "transfer": {
            "id": FAKE_VOLUME_TRANSFER_ID,
            "name": "fake-volume-transfer",
            "volume_id": "47bf04ef-1ea5-4c5f-a375-430a086d6747",
            "created_at": "2017-04-18T09:10:03.000000",
            "links": [
                {
                    "href": "fake-url-1",
                    "rel": "self"
                },
                {
                    "href": "fake-url-2",
                    "rel": "bookmark"
                }
            ]
        }
    }

    def setUp(self):
        super(TestTransfersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = transfers_client.TransfersClient(fake_auth,
                                                       'volume',
                                                       'regionOne')
        self.resource_path = 'os-volume-transfer'

    def _test_create_volume_transfer(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_VOLUME_TRANSFER_INFO)
        resp_body['transfer'].update({"auth_key": "fake-auth-key"})
        kwargs = {"name": "fake-volume-transfer",
                  "volume_id": "47bf04ef-1ea5-4c5f-a375-430a086d6747"}
        payload = json.dumps({"transfer": kwargs}, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(transfers_client.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.create_volume_transfer,
                'tempest.lib.common.rest_client.RestClient.post',
                resp_body,
                to_utf=bytes_body,
                status=202,
                mock_args=[self.resource_path, payload],
                **kwargs)

    def _test_accept_volume_transfer(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_VOLUME_TRANSFER_INFO)
        resp_body['transfer'].pop('created_at')
        kwargs = {"auth_key": "fake-auth-key"}
        payload = json.dumps({"accept": kwargs}, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(transfers_client.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.accept_volume_transfer,
                'tempest.lib.common.rest_client.RestClient.post',
                resp_body,
                to_utf=bytes_body,
                status=202,
                mock_args=['%s/%s/accept' % (self.resource_path,
                                             self.FAKE_VOLUME_TRANSFER_ID),
                           payload],
                transfer_id=self.FAKE_VOLUME_TRANSFER_ID,
                **kwargs)

    def _test_show_volume_transfer(self, bytes_body=False):
        resp_body = self.FAKE_VOLUME_TRANSFER_INFO
        self.check_service_client_function(
            self.client.show_volume_transfer,
            'tempest.lib.common.rest_client.RestClient.get',
            resp_body,
            to_utf=bytes_body,
            transfer_id="0e89cdd1-6249-421b-96d8-25fac0623d42")

    def _test_list_volume_transfers(self, detail=False, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_VOLUME_TRANSFER_INFO)
        if not detail:
            resp_body['transfer'].pop('created_at')
        resp_body = {"transfers": [resp_body['transfer']]}
        self.check_service_client_function(
            self.client.list_volume_transfers,
            'tempest.lib.common.rest_client.RestClient.get',
            resp_body,
            to_utf=bytes_body,
            detail=detail)

    def test_create_volume_transfer_with_str_body(self):
        self._test_create_volume_transfer()

    def test_create_volume_transfer_with_bytes_body(self):
        self._test_create_volume_transfer(bytes_body=True)

    def test_accept_volume_transfer_with_str_body(self):
        self._test_accept_volume_transfer()

    def test_accept_volume_transfer_with_bytes_body(self):
        self._test_accept_volume_transfer(bytes_body=True)

    def test_show_volume_transfer_with_str_body(self):
        self._test_show_volume_transfer()

    def test_show_volume_transfer_with_bytes_body(self):
        self._test_show_volume_transfer(bytes_body=True)

    def test_list_volume_transfers_with_str_body(self):
        self._test_list_volume_transfers()

    def test_list_volume_transfers_with_bytes_body(self):
        self._test_list_volume_transfers(bytes_body=True)

    def test_list_volume_transfers_with_detail_with_str_body(self):
        self._test_list_volume_transfers(detail=True)

    def test_list_volume_transfers_with_detail_with_bytes_body(self):
        self._test_list_volume_transfers(detail=True, bytes_body=True)

    def test_delete_volume_transfer(self):
        self.check_service_client_function(
            self.client.delete_volume_transfer,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=202,
            transfer_id="0e89cdd1-6249-421b-96d8-25fac0623d42")


class TestTransfersV355Client(TestTransfersClient):

    def setUp(self):
        super(TestTransfersV355Client, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = transfers_client.TransfersV355Client(fake_auth,
                                                           'volume',
                                                           'regionOne')
        self.resource_path = 'volume-transfers'
