# Copyright 2013 IBM Corporation
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

import datetime

from tempest.api.compute import base
from tempest.test import attr
import urllib


class InstanceUsageAuditLogTestJSON(base.BaseV2ComputeAdminTest):

    @classmethod
    def setUpClass(cls):
        super(InstanceUsageAuditLogTestJSON, cls).setUpClass()
        cls.adm_client = cls.os_adm.instance_usages_audit_log_client

    @attr(type='gate')
    def test_list_instance_usage_audit_logs(self):
        # list instance usage audit logs
        resp, body = self.adm_client.list_instance_usage_audit_logs()
        self.assertEqual(200, resp.status)
        expected_items = ['total_errors', 'total_instances', 'log',
                          'num_hosts_running', 'num_hosts_done',
                          'num_hosts', 'hosts_not_run', 'overall_status',
                          'period_ending', 'period_beginning',
                          'num_hosts_not_run']
        for item in expected_items:
            self.assertIn(item, body)

    @attr(type='gate')
    def test_get_instance_usage_audit_log(self):
        # Get instance usage audit log before specified time
        now = datetime.datetime.now()
        resp, body = self.adm_client.get_instance_usage_audit_log(
            urllib.quote(now.strftime("%Y-%m-%d %H:%M:%S")))

        self.assertEqual(200, resp.status)
        expected_items = ['total_errors', 'total_instances', 'log',
                          'num_hosts_running', 'num_hosts_done', 'num_hosts',
                          'hosts_not_run', 'overall_status', 'period_ending',
                          'period_beginning', 'num_hosts_not_run']
        for item in expected_items:
            self.assertIn(item, body)


class InstanceUsageAuditLogTestXML(InstanceUsageAuditLogTestJSON):
    _interface = 'xml'
