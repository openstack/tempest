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

from tempest_lib.tests import fake_auth_provider

from tempest.services.compute.json import quotas_client
from tempest.tests.services.compute import base


class TestQuotasClient(base.BaseComputeServiceTest):

    FAKE_QUOTA_SET = {
        "quota_set": {
            "injected_file_content_bytes": 10240,
            "metadata_items": 128,
            "server_group_members": 10,
            "server_groups": 10,
            "ram": 51200,
            "floating_ips": 10,
            "key_pairs": 100,
            "id": "8421f7be61064f50b680465c07f334af",
            "instances": 10,
            "security_group_rules": 20,
            "injected_files": 5,
            "cores": 20,
            "fixed_ips": -1,
            "injected_file_path_bytes": 255,
            "security_groups": 10}
        }

    project_id = "8421f7be61064f50b680465c07f334af"

    def setUp(self):
        super(TestQuotasClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = quotas_client.QuotasClient(
            fake_auth, 'compute', 'regionOne')

    def _test_show_quota_set(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_quota_set,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_QUOTA_SET,
            to_utf=bytes_body,
            tenant_id=self.project_id)

    def test_show_quota_set_with_str_body(self):
        self._test_show_quota_set()

    def test_show_quota_set_with_bytes_body(self):
        self._test_show_quota_set(bytes_body=True)

    def _test_show_default_quota_set(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_default_quota_set,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_QUOTA_SET,
            to_utf=bytes_body,
            tenant_id=self.project_id)

    def test_show_default_quota_set_with_str_body(self):
        self._test_show_quota_set()

    def test_show_default_quota_set_with_bytes_body(self):
        self._test_show_quota_set(bytes_body=True)

    def test_update_quota_set(self):
        fake_quota_set = copy.deepcopy(self.FAKE_QUOTA_SET)
        fake_quota_set['quota_set'].pop("id")
        self.check_service_client_function(
            self.client.update_quota_set,
            'tempest.common.service_client.ServiceClient.put',
            fake_quota_set,
            tenant_id=self.project_id)

    def test_delete_quota_set(self):
        self.check_service_client_function(
            self.client.delete_quota_set,
            'tempest.common.service_client.ServiceClient.delete',
            {}, status=202, tenant_id=self.project_id)
