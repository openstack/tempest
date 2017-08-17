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

    FAKE_BACKUP_UPDATE = {
        "backup": {
            "id": "4c65c15f-a5c5-464b-b92a-90e4c04636a7",
            "name": "fake-backup-name",
            "links": "fake-links"
        }
    }

    def setUp(self):
        super(TestBackupsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = backups_client.BackupsClient(fake_auth,
                                                   'volume',
                                                   'regionOne')

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
