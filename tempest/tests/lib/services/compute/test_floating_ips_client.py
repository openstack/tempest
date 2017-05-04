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

import fixtures

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import floating_ips_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestFloatingIpsClient(base.BaseServiceTest):

    floating_ip = {"fixed_ip": None,
                   "id": "46d61064-13ba-4bf0-9557-69de824c3d6f",
                   "instance_id": "a1daa443-a6bb-463e-aea2-104b7d912eb8",
                   "ip": "10.10.10.1",
                   "pool": "nova"}

    def setUp(self):
        super(TestFloatingIpsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = floating_ips_client.FloatingIPsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_floating_ips(self, bytes_body=False):
        expected = {'floating_ips': [TestFloatingIpsClient.floating_ip]}
        self.check_service_client_function(
            self.client.list_floating_ips,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body)

    def test_list_floating_ips_str_body(self):
        self._test_list_floating_ips(bytes_body=False)

    def test_list_floating_ips_byte_body(self):
        self._test_list_floating_ips(bytes_body=True)

    def _test_show_floating_ip(self, bytes_body=False):
        expected = {"floating_ip": TestFloatingIpsClient.floating_ip}
        self.check_service_client_function(
            self.client.show_floating_ip,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body,
            floating_ip_id='a1daa443-a6bb-463e-aea2-104b7d912eb8')

    def test_show_floating_ip_str_body(self):
        self._test_show_floating_ip(bytes_body=False)

    def test_show_floating_ip_byte_body(self):
        self._test_show_floating_ip(bytes_body=True)

    def _test_create_floating_ip(self, bytes_body=False):
        expected = {"floating_ip": TestFloatingIpsClient.floating_ip}
        self.check_service_client_function(
            self.client.create_floating_ip,
            'tempest.lib.common.rest_client.RestClient.post',
            expected,
            bytes_body,
            pool_name='nova')

    def test_create_floating_ip_str_body(self):
        self._test_create_floating_ip(bytes_body=False)

    def test_create_floating_ip_byte_body(self):
        self._test_create_floating_ip(bytes_body=True)

    def test_delete_floating_ip(self):
        self.check_service_client_function(
            self.client.delete_floating_ip,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, floating_ip_id='fake-id')

    def test_associate_floating_ip_to_server(self):
        self.check_service_client_function(
            self.client.associate_floating_ip_to_server,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, status=202, floating_ip='10.10.10.1',
            server_id='c782b7a9-33cd-45f0-b795-7f87f456408b')

    def test_disassociate_floating_ip_from_server(self):
        self.check_service_client_function(
            self.client.disassociate_floating_ip_from_server,
            'tempest.lib.common.rest_client.RestClient.post',
            {}, status=202, floating_ip='10.10.10.1',
            server_id='c782b7a9-33cd-45f0-b795-7f87f456408b')

    def test_is_resource_deleted_true(self):
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.compute.floating_ips_client.'
            'FloatingIPsClient.show_floating_ip',
            side_effect=lib_exc.NotFound()))
        self.assertTrue(self.client.is_resource_deleted('fake-id'))

    def test_is_resource_deleted_false(self):
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.services.compute.floating_ips_client.'
            'FloatingIPsClient.show_floating_ip',
            return_value={"floating_ip": TestFloatingIpsClient.floating_ip}))
        self.assertFalse(self.client.is_resource_deleted('fake-id'))
