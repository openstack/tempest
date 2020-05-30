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
from unittest import mock


from tempest.lib.services.compute import base_compute_client
from tempest.lib.services.compute import services_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServicesClient(base.BaseServiceTest):

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

    FAKE_UPDATE_FORCED_DOWN = {
        "service":
        {
            "forced_down": True,
            "binary": "nova-conductor",
            "host": "controller"
        }
    }

    FAKE_UPDATE_SERVICE = {
        "service": {
            "id": "e81d66a4-ddd3-4aba-8a84-171d1cb4d339",
            "binary": "nova-compute",
            "disabled_reason": "test2",
            "host": "host1",
            "state": "down",
            "status": "disabled",
            "updated_at": "2012-10-29T13:42:05.000000",
            "forced_down": False,
            "zone": "nova"
        }
    }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(
            fake_auth, 'compute', 'regionOne')
        self.addCleanup(mock.patch.stopall)

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
            host="nova-conductor", binary="controller")

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
            host="nova-conductor", binary="controller")

    def test_disable_service_with_str_body(self):
        self._test_disable_service()

    def test_disable_service_with_bytes_body(self):
        self._test_disable_service(bytes_body=True)

    def _test_log_reason_disabled_service(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_SERVICE)
        resp_body['service']['disabled_reason'] = 'test reason'

        self.check_service_client_function(
            self.client.disable_log_reason,
            'tempest.lib.common.rest_client.RestClient.put',
            resp_body,
            bytes_body,
            host="nova-conductor",
            binary="controller",
            disabled_reason='test reason')

    def _test_update_service(self, bytes_body=False, status=None,
                             disabled_reason=None, forced_down=None):
        resp_body = copy.deepcopy(self.FAKE_UPDATE_SERVICE)
        kwargs = {}

        if status is not None:
            kwargs['status'] = status
        if disabled_reason is not None:
            kwargs['disabled_reason'] = disabled_reason
        if forced_down is not None:
            kwargs['forced_down'] = forced_down

        resp_body['service'].update(kwargs)

        self.check_service_client_function(
            self.client.update_service,
            'tempest.lib.common.rest_client.RestClient.put',
            resp_body,
            bytes_body,
            service_id=resp_body['service']['id'],
            **kwargs)

    def test_log_reason_disabled_service_with_str_body(self):
        self._test_log_reason_disabled_service()

    def test_log_reason_disabled_service_with_bytes_body(self):
        self._test_log_reason_disabled_service(bytes_body=True)

    def _test_update_forced_down(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_forced_down,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_FORCED_DOWN,
            bytes_body,
            host="nova-conductor",
            binary="controller",
            forced_down=True)

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.11'))
    def test_update_forced_down_with_str_body(self, _):
        self._test_update_forced_down()

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.11'))
    def test_update_forced_down_with_bytes_body(self, _):
        self._test_update_forced_down(bytes_body=True)

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_disable_scheduling_with_str_body(self, _):
        self._test_update_service(status='disabled',
                                  disabled_reason='maintenance')

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_disable_scheduling_with_bytes_body(self, _):
        self._test_update_service(status='disabled',
                                  disabled_reason='maintenance',
                                  bytes_body=True)

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_enable_scheduling_with_str_body(self, _):
        self._test_update_service(status='enabled')

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_enable_scheduling_with_bytes_body(self, _):
        self._test_update_service(status='enabled', bytes_body=True)

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_forced_down_with_str_body(self, _):
        self._test_update_service(forced_down=True)

    @mock.patch.object(base_compute_client, 'COMPUTE_MICROVERSION',
                       new_callable=mock.PropertyMock(return_value='2.53'))
    def test_update_service_forced_down_with_bytes_body(self, _):
        self._test_update_service(forced_down=True, bytes_body=True)
