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

from tempest.lib.services.network import trunks_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTrunksClient(base.BaseServiceTest):

    FAKE_TRUNK_ID = "dfbc2103-93cf-4edf-952a-ef6deb32ddc6"
    FAKE_PORT_ID = "1f04eb36-6c84-11eb-b0ab-4fc62961629d"
    FAKE_TRUNKS = {
        "trunks": [
            {
                "admin_state_up": True,
                "description": "",
                "id": "dfbc2103-93cf-4edf-952a-ef6deb32ddc6",
                "name": "trunk0",
                "port_id": "00130aab-bb51-42a1-a7c4-6703a3a43aa5",
                "project_id": "",
                "revision_number": 2,
                "status": "DOWN",
                "sub_ports": [
                    {
                        "port_id": "87d2483d-e5e6-483d-b5f0-81b9ed1d1a91",
                        "segmentation_id": 101,
                        "segmentation_type": "vlan"
                        }
                    ],
                "tags": [],
            },
            {
                "admin_state_up": True,
                "description": "",
                "id": "9eb0e72e-11d3-4295-bcaf-6c89008d9f0a",
                "name": "trunk1",
                "port_id": "035a12bf-2ae3-42ae-8ad6-9f70640cddde",
                "project_id": "",
                "revision_number": 2,
                "status": "DOWN",
                "sub_ports": [
                    {
                        "port_id": "cba839d5-02e2-4e09-b964-81356da78165",
                        "segmentation_id": 102,
                        "segmentation_type": "vlan"
                        }
                    ],
                "tags": [],
            },
        ]
    }

    FAKE_TRUNK_1 = {
        "name": "trunk0",
        "port_id": "00130aab-bb51-42a1-a7c4-6703a3a43aa5"
    }

    def setUp(self):
        super(TestTrunksClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.trunks_client = trunks_client.TrunksClient(
            fake_auth, "network", "regionOne")

    def _test_create_trunk(self, bytes_body=False):
        self.check_service_client_function(
            self.trunks_client.create_trunk,
            "tempest.lib.common.rest_client.RestClient.post",
            {"trunk": self.FAKE_TRUNKS["trunks"][0]},
            bytes_body,
            201,
            **self.FAKE_TRUNK_1)

    def _test_list_trunks(self, bytes_body=False):
        self.check_service_client_function(
            self.trunks_client.list_trunks,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_TRUNKS,
            bytes_body,
            200)

    def _test_show_trunk(self, bytes_body=False):
        self.check_service_client_function(
            self.trunks_client.show_trunk,
            "tempest.lib.common.rest_client.RestClient.get",
            {"trunk": self.FAKE_TRUNKS["trunks"][0]},
            bytes_body,
            200,
            trunk_id=self.FAKE_TRUNK_ID)

    def _test_update_trunk(self, bytes_body=False):
        update_kwargs = {
            "admin_state_up": True,
            "name": "new_trunk"
        }

        resp_body = {
            "trunk": copy.deepcopy(
                self.FAKE_TRUNKS["trunks"][0]
            )
        }
        resp_body["trunk"].update(update_kwargs)

        self.check_service_client_function(
            self.trunks_client.update_trunk,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            trunk_id=self.FAKE_TRUNK_ID,
            **update_kwargs)

    def _test_add_subports_to_trunk(self, bytes_body=False):
        sub_ports = [{
            "port_id": "f04eb36-6c84-11eb-b0ab-4fc62961629d",
            "segmentation_type": "vlan",
            "segmentation_id": "1001"
        }]
        resp_body = copy.deepcopy(self.FAKE_TRUNKS["trunks"][0])

        resp_body["sub_ports"].append(sub_ports)
        self.check_service_client_function(
            self.trunks_client.add_subports_to_trunk,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            trunk_id=self.FAKE_TRUNK_ID,
            sub_ports=sub_ports)

    def _test_delete_subports_from_trunk(self, bytes_body=False):
        fake_sub_ports = self.FAKE_TRUNKS['trunks'][0]['sub_ports']
        sub_ports = [
            {"port_id": fake_sub_ports[0]['port_id']}
        ]
        resp_body = copy.deepcopy(self.FAKE_TRUNKS["trunks"][0])

        resp_body['sub_ports'] = []
        self.check_service_client_function(
            self.trunks_client.delete_subports_from_trunk,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            trunk_id=self.FAKE_TRUNK_ID,
            sub_ports=sub_ports)

    def test_create_trunk_with_str_body(self):
        self._test_create_trunk()

    def test_create_trunk_with_bytes_body(self):
        self._test_create_trunk(bytes_body=True)

    def test_list_trunks_with_str_body(self):
        self._test_list_trunks()

    def test_list_trunks_with_bytes_body(self):
        self._test_list_trunks(bytes_body=True)

    def test_show_trunk_with_str_body(self):
        self._test_show_trunk()

    def test_show_trunk_with_bytes_body(self):
        self._test_show_trunk(bytes_body=True)

    def test_update_trunk_with_str_body(self):
        self._test_update_trunk()

    def test_update_trunk_with_bytes_body(self):
        self._test_update_trunk(bytes_body=True)

    def test_add_subports_to_trunk_str_body(self):
        self._test_add_subports_to_trunk()

    def test_add_subports_to_trunk_bytes_body(self):
        self._test_add_subports_to_trunk(bytes_body=True)

    def test_delete_subports_from_trunk_str_body(self):
        self._test_delete_subports_from_trunk()

    def test_delete_subports_from_trunk_bytes_body(self):
        self._test_delete_subports_from_trunk(bytes_body=True)

    def test_delete_trunk(self):
        self.check_service_client_function(
            self.trunks_client.delete_trunk,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            trunk_id=self.FAKE_TRUNK_ID)
