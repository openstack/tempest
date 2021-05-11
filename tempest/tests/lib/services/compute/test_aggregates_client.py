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

from tempest.lib.services.compute import aggregates_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAggregatesClient(base.BaseServiceTest):
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
            "name": '\xf4',
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
            "name": '\xe9',
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

    FAKE_AGGREGATE = {
        "availability_zone": "nova",
        "created_at": "2013-08-18T12:17:56.297823",
        "deleted": False,
        "deleted_at": None,
        "hosts": [
            "21549b2f665945baaa7101926a00143c"
        ],
        "id": 1,
        "metadata": {
            "availability_zone": "nova"
        },
        "name": '\xe9',
        "updated_at": None
    }

    FAKE_ADD_HOST = {'aggregate': FAKE_AGGREGATE}
    FAKE_REMOVE_HOST = {'aggregate': FAKE_AGGREGATE}
    FAKE_SET_METADATA = {'aggregate': FAKE_AGGREGATE}

    def setUp(self):
        super(TestAggregatesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = aggregates_client.AggregatesClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_aggregates(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_aggregates,
            'tempest.lib.common.rest_client.RestClient.get',
            {"aggregates": []},
            bytes_body)

    def test_list_aggregates_with_str_body(self):
        self._test_list_aggregates()

    def test_list_aggregates_with_bytes_body(self):
        self._test_list_aggregates(bytes_body=True)

    def _test_show_aggregate(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_aggregate,
            'tempest.lib.common.rest_client.RestClient.get',
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
            'tempest.lib.common.rest_client.RestClient.post',
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
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, aggregate_id="1")

    def _test_update_aggregate(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_aggregate,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_AGGREGATE,
            bytes_body,
            aggregate_id=1)

    def test_update_aggregate_with_str_body(self):
        self._test_update_aggregate()

    def test_update_aggregate_with_bytes_body(self):
        self._test_update_aggregate(bytes_body=True)

    def _test_add_host(self, bytes_body=False):
        self.check_service_client_function(
            self.client.add_host,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_ADD_HOST,
            bytes_body,
            aggregate_id=1)

    def test_add_host_with_str_body(self):
        self._test_add_host()

    def test_add_host_with_bytes_body(self):
        self._test_add_host(bytes_body=True)

    def _test_remove_host(self, bytes_body=False):
        self.check_service_client_function(
            self.client.remove_host,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_REMOVE_HOST,
            bytes_body,
            aggregate_id=1)

    def test_remove_host_with_str_body(self):
        self._test_remove_host()

    def test_remove_host_with_bytes_body(self):
        self._test_remove_host(bytes_body=True)

    def _test_set_metadata(self, bytes_body=False):
        self.check_service_client_function(
            self.client.set_metadata,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SET_METADATA,
            bytes_body,
            aggregate_id=1)

    def test_set_metadata_with_str_body(self):
        self._test_set_metadata()

    def test_set_metadata_with_bytes_body(self):
        self._test_set_metadata(bytes_body=True)
