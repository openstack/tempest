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

from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class InstanceUsageAuditLogNegativeTestJSON(base.BaseV2ComputeAdminTest):

    @classmethod
    def resource_setup(cls):
        super(InstanceUsageAuditLogNegativeTestJSON, cls).resource_setup()
        cls.adm_client = cls.os_adm.instance_usages_audit_log_client

    @test.attr(type=['negative', 'gate'])
    def test_instance_usage_audit_logs_with_nonadmin_user(self):
        # the instance_usage_audit_logs API just can be accessed by admin user
        self.assertRaises(lib_exc.Unauthorized,
                          self.instance_usages_audit_log_client.
                          list_instance_usage_audit_logs)
        now = datetime.datetime.now()
        self.assertRaises(lib_exc.Unauthorized,
                          self.instance_usages_audit_log_client.
                          get_instance_usage_audit_log,
                          urllib.quote(now.strftime("%Y-%m-%d %H:%M:%S")))

    @test.attr(type=['negative', 'gate'])
    def test_get_instance_usage_audit_logs_with_invalid_time(self):
        self.assertRaises(lib_exc.BadRequest,
                          self.adm_client.get_instance_usage_audit_log,
                          "invalid_time")
