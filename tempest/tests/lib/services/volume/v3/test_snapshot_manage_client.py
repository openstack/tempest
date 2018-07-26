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

import mock

from oslo_serialization import jsonutils as json

from tempest.lib.services.volume.v3 import snapshot_manage_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSnapshotManageClient(base.BaseServiceTest):

    SNAPSHOT_MANAGE_REQUEST = {
        "snapshot": {
            "description": "snapshot-manage-description",
            "metadata": None,
            "ref": {
                "source-name": "_snapshot-22b71da0-94f9-4aca-ad45-7522b3fa96bb"
            },
            "name": "snapshot-managed",
            "volume_id": "7c064b34-1e4b-40bd-93ca-4ac5a973661b"
        }
    }

    SNAPSHOT_MANAGE_RESPONSE = {
        "snapshot": {
            "status": "creating",
            "description": "snapshot-manage-description",
            "updated_at": None,
            "volume_id": "32bafcc8-7109-42cd-8342-70d8de2bedef",
            "id": "8fd6eb9d-0a82-456d-b1ec-dea4ac7f1ee2",
            "size": 1,
            "name": "snapshot-managed",
            "created_at": "2017-07-11T10:07:58.000000",
            "metadata": {}
        }
    }

    def setUp(self):
        super(TestSnapshotManageClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = snapshot_manage_client.SnapshotManageClient(fake_auth,
                                                                  'volume',
                                                                  'regionOne')

    def _test_manage_snapshot(self, bytes_body=False):
        payload = json.dumps(self.SNAPSHOT_MANAGE_REQUEST, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(snapshot_manage_client.json,
                               'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.manage_snapshot,
                'tempest.lib.common.rest_client.RestClient.post',
                self.SNAPSHOT_MANAGE_RESPONSE,
                to_utf=bytes_body,
                status=202,
                mock_args=['os-snapshot-manage', payload],
                **self.SNAPSHOT_MANAGE_REQUEST['snapshot'])

    def test_manage_snapshot_with_str_body(self):
        self._test_manage_snapshot()

    def test_manage_snapshot_with_bytes_body(self):
        self._test_manage_snapshot(bytes_body=True)
