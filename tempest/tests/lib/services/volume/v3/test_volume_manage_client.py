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

from unittest import mock

from oslo_serialization import jsonutils as json

from tempest.lib.services.volume.v3 import volume_manage_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestVolumeManageClient(base.BaseServiceTest):

    VOLUME_MANAGE_REQUEST = {
        "volume": {
            "host": "controller1@rbd#rbd",
            "name": "volume-managed",
            "availability_zone": "nova",
            "bootable": False,
            "metadata": None,
            "ref": {
                "source-name": "volume-2ce6ca46-e6c1-4fe5-8268-3a1c536fcbf3"
            },
            "volume_type": None,
            "description": "volume-manage-description"
        }
    }

    VOLUME_MANAGE_RESPONSE = {
        "volume": {
            "migration_status": None,
            "attachments": [],
            "links": [
                {
                    "href": "fake-url-1",
                    "rel": "self"
                },
                {
                    "href": "fake-url-2",
                    "rel": "bookmark"
                }
            ],
            "availability_zone": "nova",
            "encrypted": False,
            "updated_at": None,
            "replication_status": None,
            "snapshot_id": None,
            "id": "c07cd4a4-b52b-4511-a176-fbaa2011a227",
            "size": 0,
            "user_id": "142d8663efce464c89811c63e45bd82e",
            "metadata": {},
            "status": "creating",
            "description": "volume-manage-description",
            "multiattach": False,
            "source_volid": None,
            "consistencygroup_id": None,
            "name": "volume-managed",
            "bootable": "false",
            "created_at": "2017-07-11T09:14:01.000000",
            "volume_type": None
        }
    }

    def setUp(self):
        super(TestVolumeManageClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = volume_manage_client.VolumeManageClient(fake_auth,
                                                              'volume',
                                                              'regionOne')

    def _test_manage_volume(self, bytes_body=False):
        payload = json.dumps(self.VOLUME_MANAGE_REQUEST, sort_keys=True)
        json_dumps = json.dumps

        # NOTE: Use sort_keys for json.dumps so that the expected and actual
        # payloads are guaranteed to be identical for mock_args assert check.
        with mock.patch.object(volume_manage_client.json,
                               'dumps') as mock_dumps:
            mock_dumps.side_effect = lambda d: json_dumps(d, sort_keys=True)

            self.check_service_client_function(
                self.client.manage_volume,
                'tempest.lib.common.rest_client.RestClient.post',
                self.VOLUME_MANAGE_RESPONSE,
                to_utf=bytes_body,
                status=202,
                mock_args=['os-volume-manage', payload],
                **self.VOLUME_MANAGE_REQUEST['volume'])

    def test_manage_volume_with_str_body(self):
        self._test_manage_volume()

    def test_manage_volume_with_bytes_body(self):
        self._test_manage_volume(bytes_body=True)
