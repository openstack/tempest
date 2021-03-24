# Copyright 2017 AT&T.
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

from tempest.lib.services.compute import assisted_volume_snapshots_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestVolumesClient(base.BaseServiceTest):

    FAKE_SNAPSHOT = {
        "id": "bf7b810c-70df-4c64-88a7-8588f7a6739c",
        "volumeId": "59f17c4f-66d4-4271-be40-f200523423a9"
    }

    def setUp(self):
        super(TestVolumesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = assisted_volume_snapshots_client.\
            AssistedVolumeSnapshotsClient(fake_auth, 'compute', 'regionOne')

    def _test_create_assisted_volume_snapshot(self, bytes_body=False):
        kwargs = {"type": "qcow2", "new_file": "fake_name"}
        self.check_service_client_function(
            self.client.create_assisted_volume_snapshot,
            'tempest.lib.common.rest_client.RestClient.post',
            {"snapshot": self.FAKE_SNAPSHOT},
            bytes_body, status=200, volume_id=self.FAKE_SNAPSHOT['volumeId'],
            snapshot_id=self.FAKE_SNAPSHOT['id'], **kwargs)

    def test_create_assisted_volume_snapshot_with_str_body(self):
        self._test_create_assisted_volume_snapshot()

    def test_create_assisted_volume_snapshot_with_byte_body(self):
        self._test_create_assisted_volume_snapshot(bytes_body=True)

    def test_delete_assisted_volume_snapshot(self):
        self.check_service_client_function(
            self.client.delete_assisted_volume_snapshot,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=204, volume_id=self.FAKE_SNAPSHOT['volumeId'],
            snapshot_id=self.FAKE_SNAPSHOT['id'])
