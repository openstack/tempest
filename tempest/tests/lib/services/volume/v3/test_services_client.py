# Copyright 2018 FiberHome Telecommunication Technologies CO.,LTD
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

import copy
from unittest import mock

from oslo_serialization import jsonutils as json

from tempest.lib.services.volume.v3 import services_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServicesClient(base.BaseServiceTest):

    FAKE_SERVICE_LIST = {
        "services": [
            {
                "status": "enabled",
                "binary": "cinder-backup",
                "zone": "nova",
                "state": "up",
                "updated_at": "2017-07-20T07:20:17.000000",
                "host": "fake-host",
                "disabled_reason": None
            },
            {
                "status": "enabled",
                "binary": "cinder-scheduler",
                "zone": "nova",
                "state": "up",
                "updated_at": "2017-07-20T07:20:24.000000",
                "host": "fake-host",
                "disabled_reason": None
            },
            {
                "status": "enabled",
                "binary": "cinder-volume",
                "zone": "nova",
                "frozen": False,
                "state": "up",
                "updated_at": "2017-07-20T07:20:20.000000",
                "host": "fake-host@lvm",
                "replication_status": "disabled",
                "active_backend_id": None,
                "disabled_reason": None
            }
        ]
    }

    FAKE_SERVICE_REQUEST = {
        "host": "fake-host",
        "binary": "cinder-volume"
    }

    FAKE_SERVICE_RESPONSE = {
        "disabled": False,
        "status": "enabled",
        "host": "fake-host@lvm",
        "service": "",
        "binary": "cinder-volume",
        "disabled_reason": None
    }

    def setUp(self):
        super(TestServicesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = services_client.ServicesClient(fake_auth,
                                                     'volume',
                                                     'regionOne')

    def _test_list_services(self, bytes_body=False,
                            mock_args='os-services', **params):
        self.check_service_client_function(
            self.client.list_services,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICE_LIST,
            to_utf=bytes_body,
            mock_args=[mock_args],
            **params)

    def _test_enable_service(self, bytes_body=False):
        resp_body = self.FAKE_SERVICE_RESPONSE
        kwargs = self.FAKE_SERVICE_REQUEST
        payload = json.dumps(kwargs, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(services_client.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.enable_service,
                'tempest.lib.common.rest_client.RestClient.put',
                resp_body,
                to_utf=bytes_body,
                mock_args=['os-services/enable', payload],
                **kwargs)

    def _test_disable_service(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_SERVICE_RESPONSE)
        resp_body.pop('disabled_reason')
        resp_body['disabled'] = True
        resp_body['status'] = 'disabled'
        kwargs = self.FAKE_SERVICE_REQUEST
        payload = json.dumps(kwargs, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(services_client.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.disable_service,
                'tempest.lib.common.rest_client.RestClient.put',
                resp_body,
                to_utf=bytes_body,
                mock_args=['os-services/disable', payload],
                **kwargs)

    def _test_disable_log_reason(self, bytes_body=False):
        resp_body = copy.deepcopy(self.FAKE_SERVICE_RESPONSE)
        resp_body['disabled_reason'] = "disabled for test"
        resp_body['disabled'] = True
        resp_body['status'] = 'disabled'
        kwargs = copy.deepcopy(self.FAKE_SERVICE_REQUEST)
        kwargs.update({"disabled_reason": "disabled for test"})
        payload = json.dumps(kwargs, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(services_client.json, 'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.disable_log_reason,
                'tempest.lib.common.rest_client.RestClient.put',
                resp_body,
                to_utf=bytes_body,
                mock_args=['os-services/disable-log-reason', payload],
                **kwargs)

    def _test_freeze_host(self, bytes_body=False):
        kwargs = {'host': 'host1@lvm'}
        self.check_service_client_function(
            self.client.freeze_host,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            **kwargs)

    def _test_thaw_host(self, bytes_body=False):
        kwargs = {'host': 'host1@lvm'}
        self.check_service_client_function(
            self.client.thaw_host,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            **kwargs)

    def test_list_services_with_str_body(self):
        self._test_list_services()

    def test_list_services_with_bytes_body(self):
        self._test_list_services(bytes_body=True)

    def test_list_services_with_params(self):
        mock_args = 'os-services?host=fake-host'
        self._test_list_services(mock_args=mock_args, host='fake-host')

    def test_enable_service_with_str_body(self):
        self._test_enable_service()

    def test_enable_service_with_bytes_body(self):
        self._test_enable_service(bytes_body=True)

    def test_disable_service_with_str_body(self):
        self._test_disable_service()

    def test_disable_service_with_bytes_body(self):
        self._test_disable_service(bytes_body=True)

    def test_disable_log_reason_with_str_body(self):
        self._test_disable_log_reason()

    def test_disable_log_reason_with_bytes_body(self):
        self._test_disable_log_reason(bytes_body=True)

    def test_freeze_host_with_str_body(self):
        self._test_freeze_host()

    def test_freeze_host_with_bytes_body(self):
        self._test_freeze_host(bytes_body=True)

    def test_thaw_host_with_str_body(self):
        self._test_thaw_host()

    def test_thaw_host_with_bytes_body(self):
        self._test_thaw_host(bytes_body=True)
