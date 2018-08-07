# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from tempest.lib.services.volume.v3 import limits_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestLimitsClient(base.BaseServiceTest):

    FAKE_LIMIT_INFO = {
        "limits": {
            "rate": [],
            "absolute": {
                "totalSnapshotsUsed": 0,
                "maxTotalBackups": 10,
                "maxTotalVolumeGigabytes": 1000,
                "maxTotalSnapshots": 10,
                "maxTotalBackupGigabytes": 1000,
                "totalBackupGigabytesUsed": 0,
                "maxTotalVolumes": 10,
                "totalVolumesUsed": 0,
                "totalBackupsUsed": 0,
                "totalGigabytesUsed": 0
            }
        }
    }

    def setUp(self):
        super(TestLimitsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = limits_client.LimitsClient(fake_auth,
                                                 'volume',
                                                 'regionOne')

    def _test_show_limits(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_limits,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIMIT_INFO,
            bytes_body)

    def test_show_limits_with_str_body(self):
        self._test_show_limits()

    def test_show_limits_with_bytes_body(self):
        self._test_show_limits(bytes_body=True)
