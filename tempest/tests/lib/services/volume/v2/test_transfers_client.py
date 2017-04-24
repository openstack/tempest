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

from tempest.lib.services.volume.v2 import transfers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTransfersClient(base.BaseServiceTest):

    FAKE_LIST_VOLUME_TRANSFERS_WITH_DETAIL = {
        "transfers": [{
            "created_at": "2017-04-18T09:10:03.000000",
            "volume_id": "47bf04ef-1ea5-4c5f-a375-430a086d6747",
            "id": "0e89cdd1-6249-421b-96d8-25fac0623d42",
            "links": [
                {
                    "href": "fake-url-1",
                    "rel": "self"
                },
                {
                    "href": "fake-url-2",
                    "rel": "bookmark"
                }
            ],
            "name": "fake-volume-transfer"
        }]
    }

    def setUp(self):
        super(TestTransfersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = transfers_client.TransfersClient(fake_auth,
                                                       'volume',
                                                       'regionOne')

    def _test_list_volume_transfers_with_detail(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_volume_transfers,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_VOLUME_TRANSFERS_WITH_DETAIL,
            bytes_body,
            detail=True)

    def test_list_volume_transfers_with_detail_with_str_body(self):
        self._test_list_volume_transfers_with_detail()

    def test_list_volume_transfers_with_detail_with_bytes_body(self):
        self._test_list_volume_transfers_with_detail(bytes_body=True)
