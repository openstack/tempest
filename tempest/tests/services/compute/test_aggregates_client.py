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

from tempest_lib.tests import fake_auth_provider

from tempest.services.compute.json import aggregates_client
from tempest.tests.services.compute import base


class TestAggregatesClient(base.BaseComputeServiceTest):
    FAKE_SHOW_AGGREGATE = {
        "aggregate":
        {
            "name": "hoge",
            "availability_zone": None,
            "deleted": False,
            "created_at":
            "2015-07-16T03:07:32.000000",
            "updated_at": None,
            "hosts": [],
            "deleted_at": None,
            "id": 1,
            "metadata": {}
        }
    }

    FAKE_CREATE_AGGREGATE = {
        "aggregate":
        {
            "name": u'\xf4',
            "availability_zone": None,
            "deleted": False,
            "created_at": "2015-07-21T04:11:18.000000",
            "updated_at": None,
            "deleted_at": None,
            "id": 1
        }
    }

    FAKE_UPDATE_AGGREGATE = {
        "aggregate":
        {
            "name": u'\xe9',
            "availability_zone": None,
            "deleted": False,
            "created_at": "2015-07-16T03:07:32.000000",
            "updated_at": "2015-07-23T05:16:29.000000",
            "hosts": [],
            "deleted_at": None,
            "id": 1,
            "metadata": {}
        }
    }

    def setUp(self):
        super(TestAggregatesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = aggregates_client.AggregatesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_aggregates(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_aggregates,
            'tempest.common.service_client.ServiceClient.get',
            {"aggregates": []},
            bytes_body)

    def test_list_aggregates_with_str_body(self):
        self._test_list_aggregates()

    def test_list_aggregates_with_bytes_body(self):
        self._test_list_aggregates(bytes_body=True)

    def _test_show_aggregate(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_aggregate,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_SHOW_AGGREGATE,
            bytes_body,
            aggregate_id=1)

    def test_show_aggregate_with_str_body(self):
        self._test_show_aggregate()

    def test_show_aggregate_with_bytes_body(self):
        self._test_show_aggregate(bytes_body=True)

    def _test_create_aggregate(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_aggregate,
            'tempest.common.service_client.ServiceClient.post',
            self.FAKE_CREATE_AGGREGATE,
            bytes_body,
            name='hoge')

    def test_create_aggregate_with_str_body(self):
        self._test_create_aggregate()

    def test_create_aggregate_with_bytes_body(self):
        self._test_create_aggregate(bytes_body=True)

    def test_delete_aggregate(self):
        self.check_service_client_function(
            self.client.delete_aggregate,
            'tempest.common.service_client.ServiceClient.delete',
            {}, aggregate_id="1")

    def _test_update_aggregate(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_aggregate,
            'tempest.common.service_client.ServiceClient.put',
            self.FAKE_UPDATE_AGGREGATE,
            bytes_body,
            aggregate_id=1)

    def test_update_aggregate_with_str_body(self):
        self._test_update_aggregate()

    def test_update_aggregate_with_bytes_body(self):
        self._test_update_aggregate(bytes_body=True)
