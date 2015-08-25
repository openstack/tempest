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

import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import tenant_usages_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestTenantUsagesClient(base.TestCase):

    FAKE_SERVER_USAGES = [{
        "ended_at": None,
        "flavor": "m1.tiny",
        "hours": 1.0,
        "instance_id": "1f1deceb-17b5-4c04-84c7-e0d4499c8fe0",
        "local_gb": 1,
        "memory_mb": 512,
        "name": "new-server-test",
        "started_at": "2012-10-08T20:10:44.541277",
        "state": "active",
        "tenant_id": "openstack",
        "uptime": 3600,
        "vcpus": 1
        }]

    FAKE_TENANT_USAGES = [{
        "server_usages": FAKE_SERVER_USAGES,
        "start": "2012-10-08T21:10:44.587336",
        "stop": "2012-10-08T22:10:44.587336",
        "tenant_id": "openstack",
        "total_hours": 1,
        "total_local_gb_usage": 1,
        "total_memory_mb_usage": 512,
        "total_vcpus_usage": 1
        }]

    def setUp(self):
        super(TestTenantUsagesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = tenant_usages_client.TenantUsagesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_tenant_usages(self, bytes_body=False):
        serialized_body = json.dumps({"tenant_usages":
                                      self.FAKE_TENANT_USAGES})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.list_tenant_usages()
        self.assertEqual({"tenant_usages": self.FAKE_TENANT_USAGES}, resp)

    def test_list_tenant_usages_with_str_body(self):
        self._test_list_tenant_usages()

    def test_list_tenant_usages_with_bytes_body(self):
        self._test_list_tenant_usages(bytes_body=True)

    def _test_show_tenant_usage(self, bytes_body=False):
        serialized_body = json.dumps({"tenant_usage":
                                      self.FAKE_TENANT_USAGES[0]})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_tenant_usage('openstack')
        self.assertEqual({"tenant_usage": self.FAKE_TENANT_USAGES[0]}, resp)

    def test_show_tenant_usage_with_str_body(self):
        self._test_show_tenant_usage()

    def test_show_tenant_usage_with_bytes_body(self):
        self._test_show_tenant_usage(bytes_body=True)
