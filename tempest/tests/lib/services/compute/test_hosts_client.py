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

from tempest.lib.services.compute import hosts_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestHostsClient(base.BaseServiceTest):
    FAKE_HOST_DATA = {
        "host": {
            "resource": {
                "cpu": 1,
                "disk_gb": 1028,
                "host": "c1a7de0ac9d94e4baceae031d05caae3",
                "memory_mb": 8192,
                "project": "(total)"
                }
        },
        "hosts": {
            "host_name": "c1a7de0ac9d94e4baceae031d05caae3",
            "service": "conductor",
            "zone": "internal"
        },
        "enable_hosts": {
            "host": "65c5d5b7e3bd44308e67fc50f362aee6",
            "maintenance_mode": "off_maintenance",
            "status": "enabled"
        }
        }

    FAKE_CONTROL_DATA = {
        "shutdown": {
            "host": "c1a7de0ac9d94e4baceae031d05caae3",
            "power_action": "shutdown"
        },
        "startup": {
            "host": "c1a7de0ac9d94e4baceae031d05caae3",
            "power_action": "startup"
        },
        "reboot": {
            "host": "c1a7de0ac9d94e4baceae031d05caae3",
            "power_action": "reboot"
        }}

    HOST_DATA = {'host': [FAKE_HOST_DATA['host']]}
    HOSTS_DATA = {'hosts': [FAKE_HOST_DATA['hosts']]}
    ENABLE_HOST_DATA = FAKE_HOST_DATA['enable_hosts']
    HOST_ID = "c1a7de0ac9d94e4baceae031d05caae3"
    TEST_HOST_DATA = {
        "status": "enable",
        "maintenance_mode": "disable"
    }

    def setUp(self):
        super(TestHostsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = hosts_client.HostsClient(fake_auth, 'compute',
                                               'regionOne')
        self.params = {'hostname': self.HOST_ID}
        self.func2mock = {
            'get': 'tempest.lib.common.rest_client.RestClient.get',
            'put': 'tempest.lib.common.rest_client.RestClient.put'}

    def _test_host_data(self, test_type='list', bytes_body=False):
        expected_resp = self.HOST_DATA
        if test_type != 'list':
            function_call = self.client.show_host
        else:
            expected_resp = self.HOSTS_DATA
            function_call = self.client.list_hosts
            self.params = {'host_name': self.HOST_ID}

        self.check_service_client_function(
            function_call, self.func2mock['get'],
            expected_resp, bytes_body,
            200, **self.params)

    def _test_update_hosts(self, bytes_body=False):
        expected_resp = self.ENABLE_HOST_DATA
        self.check_service_client_function(
            self.client.update_host, self.func2mock['put'],
            expected_resp, bytes_body,
            200, **self.params)

    def _test_control_host(self, control_op='reboot', bytes_body=False):
        if control_op == 'start':
            expected_resp = self.FAKE_CONTROL_DATA['startup']
            function_call = self.client.startup_host
        elif control_op == 'stop':
            expected_resp = self.FAKE_CONTROL_DATA['shutdown']
            function_call = self.client.shutdown_host
        else:
            expected_resp = self.FAKE_CONTROL_DATA['reboot']
            function_call = self.client.reboot_host

        self.check_service_client_function(
            function_call, self.func2mock['get'],
            expected_resp, bytes_body,
            200, **self.params)

    def test_show_host_with_str_body(self):
        self._test_host_data('show')

    def test_show_host_with_bytes_body(self):
        self._test_host_data('show', True)

    def test_list_host_with_str_body(self):
        self._test_host_data()

    def test_list_host_with_bytes_body(self):
        self._test_host_data(bytes_body=True)

    def test_start_host_with_str_body(self):
        self._test_control_host('start')

    def test_start_host_with_bytes_body(self):
        self._test_control_host('start', True)

    def test_stop_host_with_str_body(self):
        self._test_control_host('stop')

    def test_stop_host_with_bytes_body(self):
        self._test_control_host('stop', True)

    def test_reboot_host_with_str_body(self):
        self._test_control_host('reboot')

    def test_reboot_host_with_bytes_body(self):
        self._test_control_host('reboot', True)

    def test_update_host_with_str_body(self):
        self._test_update_hosts()

    def test_update_host_with_bytes_body(self):
        self._test_update_hosts(True)
