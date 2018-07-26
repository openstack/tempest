# Copyright 2017 AT&T Corporation.
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

from tempest.lib.services.volume.v3 import scheduler_stats_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSchedulerStatsClient(base.BaseServiceTest):
    FAKE_POOLS_LIST = {
        "pools": [
            {
                "name": "pool1",
                "capabilities": {
                    "updated": "2014-10-28T00:00:00-00:00",
                    "total_capacity": 1024,
                    "free_capacity": 100,
                    "volume_backend_name": "pool1",
                    "reserved_percentage": 0,
                    "driver_version": "1.0.0",
                    "storage_protocol": "iSCSI",
                    "QoS_support": False
                }
            },
            {
                "name": "pool2",
                "capabilities": {
                    "updated": "2014-10-28T00:00:00-00:00",
                    "total_capacity": 512,
                    "free_capacity": 200,
                    "volume_backend_name": "pool2",
                    "reserved_percentage": 0,
                    "driver_version": "1.0.2",
                    "storage_protocol": "iSER",
                    "QoS_support": True
                }
            }
        ]
    }

    def setUp(self):
        super(TestSchedulerStatsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = scheduler_stats_client.SchedulerStatsClient(
            fake_auth, 'volume', 'regionOne')

    def _test_list_pools(self, bytes_body=False, detail=False):
        resp_body = []
        if detail:
            resp_body = self.FAKE_POOLS_LIST
        else:
            resp_body = {'pools': [{'name': pool['name']}
                         for pool in self.FAKE_POOLS_LIST['pools']]}
        self.check_service_client_function(
            self.client.list_pools,
            'tempest.lib.common.rest_client.RestClient.get',
            resp_body,
            bytes_body,
            detail=detail)

    def test_list_pools_with_str_body(self):
        self._test_list_pools()

    def test_list_pools_with_str_body_and_detail(self):
        self._test_list_pools(detail=True)

    def test_list_pools_with_bytes_body(self):
        self._test_list_pools(bytes_body=True)

    def test_list_pools_with_bytes_body_and_detail(self):
        self._test_list_pools(bytes_body=True, detail=True)
