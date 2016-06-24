# Copyright 2016 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.identity.v2 import services_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServicesClient(base.BaseServiceTest):
    FAKE_SERVICE_INFO = {
        "OS-KSADM:service": {
            "id": "1",
            "name": "test",
            "type": "compute",
            "description": "test_description"
        }
    }

    FAKE_LIST_SERVICES = {
        "OS-KSADM:services": [
            {
                "id": "1",
                "name": "test",
                "type": "compute",
                "description": "test_description"
            },
            {
                "id": "2",
                "name": "test2",
                "type": "compute",
                "description": "test2_description"
            }
        ]
    }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(fake_auth,
                                                     'identity', 'regionOne')

    def _test_create_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_service,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SERVICE_INFO,
            bytes_body,
            id="1",
            name="test",
            type="compute",
            description="test_description")

    def _test_show_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_service,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICE_INFO,
            bytes_body,
            service_id="1")

    def _test_list_services(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_services,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_SERVICES,
            bytes_body)

    def test_create_service_with_str_body(self):
        self._test_create_service()

    def test_create_service_with_bytes_body(self):
        self._test_create_service(bytes_body=True)

    def test_show_service_with_str_body(self):
        self._test_show_service()

    def test_show_service_with_bytes_body(self):
        self._test_show_service(bytes_body=True)

    def test_delete_service(self):
        self.check_service_client_function(
            self.client.delete_service,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            service_id="1",
            status=204)
