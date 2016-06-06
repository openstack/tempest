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

import datetime

from tempest.lib.services.compute import instance_usage_audit_log_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestInstanceUsagesAuditLogClient(base.BaseServiceTest):

    FAKE_AUDIT_LOG = {
        "hosts_not_run": [
            "f4eb7cfd155f4574967f8b55a7faed75"
        ],
        "log": {},
        "num_hosts": 1,
        "num_hosts_done": 0,
        "num_hosts_not_run": 1,
        "num_hosts_running": 0,
        "overall_status": "0 of 1 hosts done. 0 errors.",
        "period_beginning": "2012-12-01 00:00:00",
        "period_ending": "2013-01-01 00:00:00",
        "total_errors": 0,
        "total_instances": 0
    }

    def setUp(self):
        super(TestInstanceUsagesAuditLogClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = (instance_usage_audit_log_client.
                       InstanceUsagesAuditLogClient(fake_auth, 'compute',
                                                    'regionOne'))

    def _test_list_instance_usage_audit_logs(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_instance_usage_audit_logs,
            'tempest.lib.common.rest_client.RestClient.get',
            {"instance_usage_audit_logs": self.FAKE_AUDIT_LOG},
            bytes_body)

    def test_list_instance_usage_audit_logs_with_str_body(self):
        self._test_list_instance_usage_audit_logs()

    def test_list_instance_usage_audit_logs_with_bytes_body(self):
        self._test_list_instance_usage_audit_logs(bytes_body=True)

    def _test_show_instance_usage_audit_log(self, bytes_body=False):
        before_time = datetime.datetime(2012, 12, 1, 0, 0)
        self.check_service_client_function(
            self.client.show_instance_usage_audit_log,
            'tempest.lib.common.rest_client.RestClient.get',
            {"instance_usage_audit_log": self.FAKE_AUDIT_LOG},
            bytes_body,
            time_before=before_time)

    def test_show_instance_usage_audit_log_with_str_body(self):
        self._test_show_instance_usage_audit_log()

    def test_show_network_with_bytes_body_with_bytes_body(self):
        self._test_show_instance_usage_audit_log(bytes_body=True)
