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

from six.moves.urllib import parse as urllib

from tempest.api.compute import base
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class InstanceUsageAuditLogNegativeTestJSON(base.BaseV2ComputeAdminTest):
    """Negative tests of instance usage audit logs"""

    @classmethod
    def setup_clients(cls):
        super(InstanceUsageAuditLogNegativeTestJSON, cls).setup_clients()
        cls.adm_client = cls.os_admin.instance_usages_audit_log_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a9d33178-d2c9-4131-ad3b-f4ca8d0308a2')
    def test_instance_usage_audit_logs_with_nonadmin_user(self):
        """Test list/show instance usage audit logs by non-admin should fail

        The instance_usage_audit_logs API just can be accessed by admin user.
        """
        self.assertRaises(lib_exc.Forbidden,
                          self.instance_usages_audit_log_client.
                          list_instance_usage_audit_logs)
        now = datetime.datetime.now()
        self.assertRaises(lib_exc.Forbidden,
                          self.instance_usages_audit_log_client.
                          show_instance_usage_audit_log,
                          urllib.quote(now.strftime("%Y-%m-%d %H:%M:%S")))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9b952047-3641-41c7-ba91-a809fc5974c8')
    def test_get_instance_usage_audit_logs_with_invalid_time(self):
        """Test showing instance usage audit logs with invalid time

        Showing instance usage audit logs with invalid time should fail.
        """
        self.assertRaises(lib_exc.BadRequest,
                          self.adm_client.show_instance_usage_audit_log,
                          "invalid_time")
