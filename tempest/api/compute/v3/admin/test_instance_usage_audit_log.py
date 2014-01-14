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
import urllib

from tempest.api.compute import base
from tempest import test


class InstanceUsageAuditLogV3TestJSON(base.BaseV3ComputeAdminTest):

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(InstanceUsageAuditLogV3TestJSON, cls).setUpClass()
        cls.adm_client = cls.instance_usages_audit_log_admin_client

    @test.attr(type='gate')
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

    @test.attr(type='gate')
    def test_list_instance_usage_audit_logs_with_filter_before(self):
        # Get instance usage audit log before specified time
        ending_time = datetime.datetime(2012, 12, 24)
        resp, body = self.adm_client.list_instance_usage_audit_logs(
            urllib.quote(ending_time.strftime("%Y-%m-%d %H:%M:%S")))

        self.assertEqual(200, resp.status)
        expected_items = ['total_errors', 'total_instances', 'log',
                          'num_hosts_running', 'num_hosts_done', 'num_hosts',
                          'hosts_not_run', 'overall_status', 'period_ending',
                          'period_beginning', 'num_hosts_not_run']
        for item in expected_items:
            self.assertIn(item, body)
        self.assertEqual(body['period_ending'], "2012-12-23 23:00:00")


class InstanceUsageAuditLogV3TestXML(InstanceUsageAuditLogV3TestJSON):
    _interface = 'xml'
