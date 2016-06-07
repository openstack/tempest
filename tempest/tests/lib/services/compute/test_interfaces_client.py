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

from tempest.lib.services.compute import interfaces_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestInterfacesClient(base.BaseServiceTest):
    # Data Values to be used for testing #
    FAKE_INTERFACE_DATA = {
        "fixed_ips": [{
            "ip_address": "192.168.1.1",
            "subnet_id": "f8a6e8f8-c2ec-497c-9f23-da9616de54ef"
            }],
        "mac_addr": "fa:16:3e:4c:2c:30",
        "net_id": "3cb9bc59-5699-4588-a4b1-b87f96708bc6",
        "port_id": "ce531f90-199f-48c0-816c-13e38010b442",
        "port_state": "ACTIVE"}

    FAKE_SHOW_DATA = {
        "interfaceAttachment": FAKE_INTERFACE_DATA}
    FAKE_LIST_DATA = {
        "interfaceAttachments": [FAKE_INTERFACE_DATA]}

    FAKE_SERVER_ID = "ec14c864-096e-4e27-bb8a-2c2b4dc6f3f5"
    FAKE_PORT_ID = FAKE_SHOW_DATA['interfaceAttachment']['port_id']
    func2mock = {
        'delete': 'tempest.lib.common.rest_client.RestClient.delete',
        'get': 'tempest.lib.common.rest_client.RestClient.get',
        'post': 'tempest.lib.common.rest_client.RestClient.post'}

    def setUp(self):
        super(TestInterfacesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = interfaces_client.InterfacesClient(fake_auth,
                                                         "compute",
                                                         "regionOne")

    def _test_interface_operation(self, operation="create", bytes_body=False):
        response_code = 200
        expected_op = self.FAKE_SHOW_DATA
        mock_operation = self.func2mock['get']
        params = {'server_id': self.FAKE_SERVER_ID,
                  'port_id': self.FAKE_PORT_ID}
        if operation == 'list':
            expected_op = self.FAKE_LIST_DATA
            function = self.client.list_interfaces
            params = {'server_id': self.FAKE_SERVER_ID}
        elif operation == 'show':
            function = self.client.show_interface
        elif operation == 'delete':
            expected_op = {}
            mock_operation = self.func2mock['delete']
            function = self.client.delete_interface
            response_code = 202
        else:
            function = self.client.create_interface
            mock_operation = self.func2mock['post']

        self.check_service_client_function(
            function, mock_operation, expected_op,
            bytes_body, response_code, **params)

    def test_list_interfaces_with_str_body(self):
        self._test_interface_operation('list')

    def test_list_interfaces_with_bytes_body(self):
        self._test_interface_operation('list', True)

    def test_show_interface_with_str_body(self):
        self._test_interface_operation('show')

    def test_show_interface_with_bytes_body(self):
        self._test_interface_operation('show', True)

    def test_delete_interface_with_str_body(self):
        self._test_interface_operation('delete')

    def test_delete_interface_with_bytes_body(self):
        self._test_interface_operation('delete', True)

    def test_create_interface_with_str_body(self):
        self._test_interface_operation()

    def test_create_interface_with_bytes_body(self):
        self._test_interface_operation(bytes_body=True)
