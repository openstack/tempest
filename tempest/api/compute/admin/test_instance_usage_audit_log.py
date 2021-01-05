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
from urllib import parse as urllib

from tempest.api.compute import base
from tempest.lib import decorators


class InstanceUsageAuditLogTestJSON(base.BaseV2ComputeAdminTest):
    """Test instance usage audit logs API"""

    @classmethod
    def setup_clients(cls):
        super(InstanceUsageAuditLogTestJSON, cls).setup_clients()
        cls.adm_client = cls.os_admin.instance_usages_audit_log_client

    @decorators.idempotent_id('25319919-33d9-424f-9f99-2c203ee48b9d')
    def test_list_instance_usage_audit_logs(self):
        """Test listing instance usage audit logs"""
        self.adm_client.list_instance_usage_audit_logs()

    @decorators.idempotent_id('6e40459d-7c5f-400b-9e83-449fbc8e7feb')
    def test_get_instance_usage_audit_log(self):
        """Test getting instance usage audit log before specified time"""
        now = datetime.datetime.now()
        self.adm_client.show_instance_usage_audit_log(
            urllib.quote(now.strftime("%Y-%m-%d %H:%M:%S")))
