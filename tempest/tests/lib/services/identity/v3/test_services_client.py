# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import services_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServicesClient(base.BaseServiceTest):
    FAKE_CREATE_SERVICE = {
        "service": {
            "type": "compute",
            "name": "compute2",
            "description": "Compute service 2"
            }
        }

    FAKE_SERVICE_INFO = {
        "service": {
            "description": "Keystone Identity Service",
            "enabled": True,
            "id": "686766",
            "links": {
                "self": "http://example.com/identity/v3/services/686766"
                },
            "name": "keystone",
            "type": "identity"
            }
        }

    FAKE_LIST_SERVICES = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/services"
            },
        "services": [
            {
                "description": "Nova Compute Service",
                "enabled": True,
                "id": "1999c3",
                "links": {
                    "self": "http://example.com/identity/v3/services/1999c3"
                    },
                "name": "nova",
                "type": "compute"
                },
            {
                "description": "Cinder Volume Service V2",
                "enabled": True,
                "id": "392166",
                "links": {
                    "self": "http://example.com/identity/v3/services/392166"
                    },
                "name": "cinderv2",
                "type": "volumev2"
                },
            {
                "description": "Neutron Service",
                "enabled": True,
                "id": "4fe41a",
                "links": {
                    "self": "http://example.com/identity/v3/services/4fe41a"
                    },
                "name": "neutron",
                "type": "network"
                }
        ]
    }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(fake_auth, 'identity',
                                                     'regionOne')

    def _test_create_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_service,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SERVICE,
            bytes_body,
            status=201)

    def _test_show_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_service,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICE_INFO,
            bytes_body,
            service_id="686766")

    def _test_list_services(self, bytes_body=False, mock_args='services',
                            **params):
        self.check_service_client_function(
            self.client.list_services,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_SERVICES,
            bytes_body,
            mock_args=[mock_args],
            **params)

    def _test_update_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_service,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_SERVICE_INFO,
            bytes_body,
            service_id="686766")

    def test_create_service_with_str_body(self):
        self._test_create_service()

    def test_create_service_with_bytes_body(self):
        self._test_create_service(bytes_body=True)

    def test_show_service_with_str_body(self):
        self._test_show_service()

    def test_show_service_with_bytes_body(self):
        self._test_show_service(bytes_body=True)

    def test_list_services_with_str_body(self):
        self._test_list_services()

    def test_list_services_with_bytes_body(self):
        self._test_list_services(bytes_body=True)

    def test_list_services_with_params(self):
        self._test_list_services(
            type='fake-type', mock_args='services?type=fake-type')

    def test_update_service_with_str_body(self):
        self._test_update_service()

    def test_update_service_with_bytes_body(self):
        self._test_update_service(bytes_body=True)

    def test_delete_service(self):
        self.check_service_client_function(
            self.client.delete_service,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            service_id="686766",
            status=204)
