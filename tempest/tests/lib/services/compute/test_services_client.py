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

from tempest.lib.services.compute import services_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestServicesClient(base.BaseComputeServiceTest):

    FAKE_SERVICES = {
        "services":
        [{
            "status": "enabled",
            "binary": "nova-conductor",
            "zone": "internal",
            "state": "up",
            "updated_at": "2015-08-19T06:50:55.000000",
            "host": "controller",
            "disabled_reason": None,
            "id": 1
        }]
    }

    FAKE_SERVICE = {
        "service":
        {
            "status": "enabled",
            "binary": "nova-conductor",
            "host": "controller"
        }
    }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(
            fake_auth, 'compute', 'regionOne')

    def test_list_services_with_str_body(self):
        self.check_service_client_function(
            self.client.list_services,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICES)

    def test_list_services_with_bytes_body(self):
        self.check_service_client_function(
            self.client.list_services,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICES, to_utf=True)

    def _test_enable_service(self, bytes_body=False):
        self.check_service_client_function(
            self.client.enable_service,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_SERVICE,
            bytes_body,
            host_name="nova-conductor", binary="controller")

    def test_enable_service_with_str_body(self):
        self._test_enable_service()

    def test_enable_service_with_bytes_body(self):
        self._test_enable_service(bytes_body=True)

    def _test_disable_service(self, bytes_body=False):
        fake_service = copy.deepcopy(self.FAKE_SERVICE)
        fake_service["service"]["status"] = "disable"

        self.check_service_client_function(
            self.client.disable_service,
            'tempest.lib.common.rest_client.RestClient.put',
            fake_service,
            bytes_body,
            host_name="nova-conductor", binary="controller")

    def test_disable_service_with_str_body(self):
        self._test_disable_service()

    def test_disable_service_with_bytes_body(self):
        self._test_disable_service(bytes_body=True)
