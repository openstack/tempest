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

from oslotest import mockpatch
from tempest.tests.lib import fake_auth_provider

from tempest.lib.services.compute import server_groups_client
from tempest.tests.lib import fake_http
from tempest.tests.lib.services.compute import base


class TestServerGroupsClient(base.BaseComputeServiceTest):

    server_group = {
        "id": "5bbcc3c4-1da2-4437-a48a-66f15b1b13f9",
        "name": "test",
        "policies": ["anti-affinity"],
        "members": [],
        "metadata": {}}

    def setUp(self):
        super(TestServerGroupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = server_groups_client.ServerGroupsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_server_group(self, bytes_body=False):
        expected = {"server_group": TestServerGroupsClient.server_group}
        self.check_service_client_function(
            self.client.create_server_group,
            'tempest.lib.common.rest_client.RestClient.post', expected,
            bytes_body, name='fake-group', policies=['affinity'])

    def test_create_server_group_str_body(self):
        self._test_create_server_group(bytes_body=False)

    def test_create_server_group_byte_body(self):
        self._test_create_server_group(bytes_body=True)

    def test_delete_server_group(self):
        response = fake_http.fake_http_response({}, status=204), ''
        self.useFixture(mockpatch.Patch(
            'tempest.lib.common.rest_client.RestClient.delete',
            return_value=response))
        self.client.delete_server_group('fake-group')

    def _test_list_server_groups(self, bytes_body=False):
        expected = {"server_groups": [TestServerGroupsClient.server_group]}
        self.check_service_client_function(
            self.client.list_server_groups,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body)

    def test_list_server_groups_str_body(self):
        self._test_list_server_groups(bytes_body=False)

    def test_list_server_groups_byte_body(self):
        self._test_list_server_groups(bytes_body=True)

    def _test_show_server_group(self, bytes_body=False):
        expected = {"server_group": TestServerGroupsClient.server_group}
        self.check_service_client_function(
            self.client.show_server_group,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body,
            server_group_id='5bbcc3c4-1da2-4437-a48a-66f15b1b13f9')

    def test_show_server_group_str_body(self):
        self._test_show_server_group(bytes_body=False)

    def test_show_server_group_byte_body(self):
        self._test_show_server_group(bytes_body=True)
