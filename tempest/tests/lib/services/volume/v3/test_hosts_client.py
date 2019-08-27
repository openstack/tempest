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

from tempest.lib.services.volume.v3 import hosts_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestHostsClient(base.BaseServiceTest):
    FAKE_LIST_HOSTS = {
        "hosts": [
            {
                "service-status": "available",
                "service": "cinder-scheduler",
                "zone": "nova",
                "service-state": "enabled",
                "host_name": "fake-host",
                "last-update": "2017-04-12T04:26:03.000000"
            },
            {
                "service-status": "available",
                "service": "cinder-volume",
                "zone": "nova",
                "service-state": "enabled",
                "host_name": "fake-host@rbd",
                "last-update": "2017-04-12T04:26:07.000000"
            }
        ]
    }

    FAKE_HOST_INFO = {
        "host": [
            {
                "resource": {
                    "volume_count": "2",
                    "total_volume_gb": "2",
                    "total_snapshot_gb": "0",
                    "project": "(total)",
                    "host": "fake-host@rbd",
                    "snapshot_count": "0"
                }
            },
            {
                "resource": {
                    "volume_count": "2",
                    "total_volume_gb": "2",
                    "total_snapshot_gb": "0",
                    "project": "f21a9c86d7114bf99c711f4874d80474",
                    "host": "fake-host@lvm",
                    "snapshot_count": "0"
                }
            }
        ]
    }

    def setUp(self):
        super(TestHostsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = hosts_client.HostsClient(fake_auth,
                                               'volume',
                                               'regionOne')

    def _test_list_hosts(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_hosts,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_HOSTS, bytes_body)

    def _test_show_host(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_host,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_HOST_INFO, bytes_body, host_name='fake-host')

    def test_list_hosts_with_str_body(self):
        self._test_list_hosts()

    def test_list_hosts_with_bytes_body(self):
        self._test_list_hosts(bytes_body=True)

    def test_show_host_with_str_body(self):
        self._test_show_host()

    def test_show_host_with_bytes_body(self):
        self._test_show_host(bytes_body=True)
