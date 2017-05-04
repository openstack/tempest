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

import fixtures

from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import snapshots_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSnapshotsClient(base.BaseServiceTest):

    FAKE_SNAPSHOT = {
        "createdAt": "2015-10-02T16:27:54.724209",
        "displayDescription": u"Another \u1234.",
        "displayName": u"v\u1234-001",
        "id": "100",
        "size": 100,
        "status": "available",
        "volumeId": "12"
    }

    FAKE_SNAPSHOTS = {"snapshots": [FAKE_SNAPSHOT]}

    def setUp(self):
        super(TestSnapshotsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = snapshots_client.SnapshotsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_snapshot,
            'tempest.lib.common.rest_client.RestClient.post',
            {"snapshot": self.FAKE_SNAPSHOT},
            to_utf=bytes_body, status=200,
            volume_id=self.FAKE_SNAPSHOT["volumeId"])

    def test_create_snapshot_with_str_body(self):
        self._test_create_snapshot()

    def test_create_shapshot_with_bytes_body(self):
        self._test_create_snapshot(bytes_body=True)

    def _test_show_snapshot(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_snapshot,
            'tempest.lib.common.rest_client.RestClient.get',
            {"snapshot": self.FAKE_SNAPSHOT},
            to_utf=bytes_body, snapshot_id=self.FAKE_SNAPSHOT["id"])

    def test_show_snapshot_with_str_body(self):
        self._test_show_snapshot()

    def test_show_snapshot_with_bytes_body(self):
        self._test_show_snapshot(bytes_body=True)

    def _test_list_snapshots(self, bytes_body=False, **params):
        self.check_service_client_function(
            self.client.list_snapshots,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SNAPSHOTS, to_utf=bytes_body, **params)

    def test_list_snapshots_with_str_body(self):
        self._test_list_snapshots()

    def test_list_snapshots_with_byte_body(self):
        self._test_list_snapshots(bytes_body=True)

    def test_list_snapshots_with_params(self):
        self._test_list_snapshots('fake')

    def test_delete_snapshot(self):
        self.check_service_client_function(
            self.client.delete_snapshot,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=202, snapshot_id=self.FAKE_SNAPSHOT['id'])

    def test_is_resource_deleted_true(self):
        module = ('tempest.lib.services.compute.snapshots_client.'
                  'SnapshotsClient.show_snapshot')
        self.useFixture(fixtures.MockPatch(
            module, side_effect=lib_exc.NotFound))
        self.assertTrue(self.client.is_resource_deleted('fake-id'))

    def test_is_resource_deleted_false(self):
        module = ('tempest.lib.services.compute.snapshots_client.'
                  'SnapshotsClient.show_snapshot')
        self.useFixture(fixtures.MockPatch(
            module, return_value={}))
        self.assertFalse(self.client.is_resource_deleted('fake-id'))
