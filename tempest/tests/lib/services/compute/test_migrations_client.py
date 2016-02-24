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

from tempest.lib.services.compute import migrations_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestMigrationsClient(base.BaseComputeServiceTest):
    FAKE_MIGRATION_INFO = {"migrations": [{
        "created_at": "2012-10-29T13:42:02",
        "dest_compute": "compute2",
        "dest_host": "1.2.3.4",
        "dest_node": "node2",
        "id": 1234,
        "instance_uuid": "e9e4fdd7-f956-44ff-bfeb-d654a96ab3a2",
        "new_instance_type_id": 2,
        "old_instance_type_id": 1,
        "source_compute": "compute1",
        "source_node": "node1",
        "status": "finished",
        "updated_at": "2012-10-29T13:42:02"}]}

    def setUp(self):
        super(TestMigrationsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.mg_client_obj = migrations_client.MigrationsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_migrations(self, bytes_body=False):
        self.check_service_client_function(
            self.mg_client_obj.list_migrations,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_MIGRATION_INFO,
            bytes_body)

    def test_list_migration_with_str_body(self):
        self._test_list_migrations()

    def test_list_migration_with_bytes_body(self):
        self._test_list_migrations(True)
