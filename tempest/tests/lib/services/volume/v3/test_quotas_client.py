# Copyright 2016 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.volume.v3 import quotas_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestQuotasClient(base.BaseServiceTest):
    FAKE_QUOTAS = {
        "quota_set": {
            "id": '730a1cbd-68ca-4d68-8e09-d603f2dfa72b',
            "gigabytes": 5,
            "snapshots": 10,
            "volumes": 20,
            'backups': 10,
            'groups': 10,
            'per_volume_gigabytes': 1000,
            'backup_gigabytes': 2000
        }
    }

    FAKE_UPDATE_QUOTAS_RESPONSE = {
        "quota_set": {
            "gigabytes": 6,
            "snapshots": 11,
            "volumes": 21,
            'backups': 11,
            'groups': 11,
            'per_volume_gigabytes': 1001,
            'backup_gigabytes': 2001
        }
    }

    def setUp(self):
        super(TestQuotasClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = quotas_client.QuotasClient(fake_auth,
                                                 'volume',
                                                 'regionOne')

    def _test_show_default_quota_set(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_default_quota_set,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_QUOTAS,
            bytes_body, tenant_id="fake_tenant")

    def _test_show_quota_set(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_quota_set,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_QUOTAS,
            bytes_body, tenant_id="fake_tenant")

    def _test_update_quota_set(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_quota_set,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_QUOTAS_RESPONSE,
            bytes_body, tenant_id="fake_tenant")

    def test_show_default_quota_set_with_str_body(self):
        self._test_show_default_quota_set()

    def test_show_default_quota_set_with_bytes_body(self):
        self._test_show_default_quota_set(bytes_body=True)

    def test_show_quota_set_with_str_body(self):
        self._test_show_quota_set()

    def test_show_quota_set_with_bytes_body(self):
        self._test_show_quota_set(bytes_body=True)

    def test_update_quota_set_with_str_body(self):
        self._test_update_quota_set()

    def test_update_quota_set_with_bytes_body(self):
        self._test_update_quota_set(bytes_body=True)

    def test_delete_quota_set(self):
        self.check_service_client_function(
            self.client.delete_quota_set,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            tenant_id="fake_tenant")
