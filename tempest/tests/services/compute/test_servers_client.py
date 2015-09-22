# Copyright 2015 IBM Corp.
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

from tempest.services.compute.json import servers_client
from tempest.tests import fake_auth_provider
from tempest.tests.services.compute import base


class TestServersClient(base.BaseComputeServiceTest):

    FAKE_SERVERS = {'servers': [{
        "id": "616fb98f-46ca-475e-917e-2563e5a8cd19",
        "links": [
            {
                "href": "http://os.co/v2/616fb98f-46ca-475e-917e-2563e5a8cd19",
                "rel": "self"
            },
            {
                "href": "http://os.co/616fb98f-46ca-475e-917e-2563e5a8cd19",
                "rel": "bookmark"
            }
        ],
        "name": u"new\u1234-server-test"}]
    }

    FAKE_SERVER_GET = {'server': {
        "accessIPv4": "",
        "accessIPv6": "",
        "addresses": {
            "private": [
                {
                    "addr": "192.168.0.3",
                    "version": 4
                }
            ]
        },
        "created": "2012-08-20T21:11:09Z",
        "flavor": {
            "id": "1",
            "links": [
                {
                    "href": "http://os.com/openstack/flavors/1",
                    "rel": "bookmark"
                }
            ]
        },
        "hostId": "65201c14a29663e06d0748e561207d998b343e1d164bfa0aafa9c45d",
        "id": "893c7791-f1df-4c3d-8383-3caae9656c62",
        "image": {
            "id": "70a599e0-31e7-49b7-b260-868f441e862b",
            "links": [
                {
                    "href": "http://imgs/70a599e0-31e7-49b7-b260-868f441e862b",
                    "rel": "bookmark"
                }
            ]
        },
        "links": [
            {
                "href": "http://v2/srvs/893c7791-f1df-4c3d-8383-3caae9656c62",
                "rel": "self"
            },
            {
                "href": "http://srvs/893c7791-f1df-4c3d-8383-3caae9656c62",
                "rel": "bookmark"
            }
        ],
        "metadata": {
            u"My Server N\u1234me": u"Apa\u1234che1"
        },
        "name": u"new\u1234-server-test",
        "progress": 0,
        "status": "ACTIVE",
        "tenant_id": "openstack",
        "updated": "2012-08-20T21:11:09Z",
        "user_id": "fake"}
    }

    FAKE_SERVER_POST = {"server": {
        "id": "616fb98f-46ca-475e-917e-2563e5a8cd19",
        "adminPass": "fake-admin-pass",
        "security_groups": [
            'fake-security-group-1',
            'fake-security-group-2'
        ],
        "links": [
            {
                "href": "http://os.co/v2/616fb98f-46ca-475e-917e-2563e5a8cd19",
                "rel": "self"
            },
            {
                "href": "http://os.co/616fb98f-46ca-475e-917e-2563e5a8cd19",
                "rel": "bookmark"
            }
        ],
        "OS-DCF:diskConfig": "fake-disk-config"}
    }

    FAKE_ADDRESS = {"addresses": {
        "private": [
            {
                "addr": "192.168.0.3",
                "version": 4
            }
        ]}
    }

    server_id = FAKE_SERVER_GET['server']['id']
    network_id = 'a6b0875b-6b5d-4a5a-81eb-0c3aa62e5fdb'

    def setUp(self):
        super(TestServersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = servers_client.ServersClient(
            fake_auth, 'compute', 'regionOne')

    def test_list_servers_with_str_body(self):
        self._test_list_servers()

    def test_list_servers_with_bytes_body(self):
        self._test_list_servers(bytes_body=True)

    def _test_list_servers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_servers,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_SERVERS,
            bytes_body)

    def test_show_server_with_str_body(self):
        self._test_show_server()

    def test_show_server_with_bytes_body(self):
        self._test_show_server(bytes_body=True)

    def _test_show_server(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_server,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_SERVER_GET,
            bytes_body,
            server_id=self.server_id
            )

    def test_delete_server(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_server,
            'tempest.common.service_client.ServiceClient.delete',
            {},
            status=204,
            server_id=self.server_id
            )

    def test_create_server_with_str_body(self):
        self._test_create_server()

    def test_create_server_with_bytes_body(self):
        self._test_create_server(True)

    def _test_create_server(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_server,
            'tempest.common.service_client.ServiceClient.post',
            self.FAKE_SERVER_POST,
            bytes_body,
            status=202,
            name='fake-name',
            imageRef='fake-image-ref',
            flavorRef='fake-flavor-ref'
            )

    def test_list_addresses_with_str_body(self):
        self._test_list_addresses()

    def test_list_addresses_with_bytes_body(self):
        self._test_list_addresses(True)

    def _test_list_addresses(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_addresses,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_ADDRESS,
            bytes_body,
            server_id=self.server_id
            )

    def test_list_addresses_by_network_with_str_body(self):
        self._test_list_addresses_by_network()

    def test_list_addresses_by_network_with_bytes_body(self):
        self._test_list_addresses_by_network(True)

    def _test_list_addresses_by_network(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_addresses_by_network,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_ADDRESS['addresses'],
            bytes_body,
            server_id=self.server_id,
            network_id=self.network_id
            )
