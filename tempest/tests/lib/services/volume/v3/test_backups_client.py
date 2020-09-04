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

from tempest.lib.services.volume.v3 import backups_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestBackupsClient(base.BaseServiceTest):

    FAKE_BACKUP_LIST = {
        "backups": [
            {
                "id": "2ef47aee-8844-490c-804d-2a8efe561c65",
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
                "name": "backup001"
            }
        ]
    }

    FAKE_BACKUP_LIST_WITH_DETAIL = {
        "backups": [
            {
                "availability_zone": "az1",
                "container": "volumebackups",
                "created_at": "2013-04-02T10:35:27.000000",
                "updated_at": "2013-04-02T10:39:27.000000",
                "data_timestamp": "2013-04-02T10:35:27.000000",
                "description": None,
                "fail_reason": None,
                "id": "2ef47aee-8844-490c-804d-2a8efe561c65",
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
                "name": "backup001",
                "object_count": 22,
                "os-backup-project-attr:project_id": "2c67a14be9314c5dae2ee6",
                "user_id": "515ba0dd59f84f25a6a084a45d8d93b2",
                "size": 1,
                "status": "available",
                "volume_id": "e5185058-943a-4cb4-96d9-72c184c337d6",
                "is_incremental": True,
                "has_dependent_backups": False
            }
        ]
    }

    FAKE_BACKUP_UPDATE = {
        "backup": {
            "id": "4c65c15f-a5c5-464b-b92a-90e4c04636a7",
            "name": "fake-backup-name",
            "links": [
                {
                    "href": "fake-url-1",
                    "rel": "self"
                },
                {
                    "href": "fake-url-2",
                    "rel": "bookmark"
                }
            ]
        }
    }

    def setUp(self):
        super(TestBackupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = backups_client.BackupsClient(fake_auth,
                                                   'volume',
                                                   'regionOne')

    def _test_list_backups(self, detail=False, mock_args='backups',
                           bytes_body=False, **params):
        if detail:
            resp_body = self.FAKE_BACKUP_LIST_WITH_DETAIL
        else:
            resp_body = self.FAKE_BACKUP_LIST
        self.check_service_client_function(
            self.client.list_backups,
            'tempest.lib.common.rest_client.RestClient.get',
            resp_body,
            to_utf=bytes_body,
            mock_args=[mock_args],
            detail=detail,
            **params)

    def test_list_backups_with_str_body(self):
        self._test_list_backups()

    def test_list_backups_with_bytes_body(self):
        self._test_list_backups(bytes_body=True)

    def test_list_backups_with_detail_with_str_body(self):
        mock_args = "backups/detail"
        self._test_list_backups(detail=True, mock_args=mock_args)

    def test_list_backups_with_detail_with_bytes_body(self):
        mock_args = "backups/detail"
        self._test_list_backups(detail=True, mock_args=mock_args,
                                bytes_body=True)

    def test_list_backups_with_params(self):
        # Run the test separately for each param, to avoid assertion error
        # resulting from randomized params order.
        mock_args = 'backups?sort_key=name'
        self._test_list_backups(mock_args=mock_args, sort_key='name')

        mock_args = 'backups/detail?limit=10'
        self._test_list_backups(detail=True, mock_args=mock_args,
                                bytes_body=True, limit=10)

    def _test_update_backup(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_backup,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_BACKUP_UPDATE,
            bytes_body,
            backup_id='4c65c15f-a5c5-464b-b92a-90e4c04636a7')

    def test_update_backup_with_str_body(self):
        self._test_update_backup()

    def test_update_backup_with_bytes_body(self):
        self._test_update_backup(bytes_body=True)
