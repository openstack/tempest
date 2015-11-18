# Copyright (C) 2017 Dell Inc. or its subsidiaries.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.volume.v3 import group_types_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestGroupTypesClient(base.BaseServiceTest):
    FAKE_CREATE_GROUP_TYPE = {
        "group_type": {
            "name": "group-type-001",
            "description": "Test group type 1",
            "group_specs": {},
            "is_public": True,
        }
    }

    def setUp(self):
        super(TestGroupTypesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = group_types_client.GroupTypesClient(fake_auth,
                                                          'volume',
                                                          'regionOne')

    def _test_create_group_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_group_type,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_GROUP_TYPE,
            bytes_body,
            status=202)

    def test_create_group_type_with_str_body(self):
        self._test_create_group_type()

    def test_create_group_type_with_bytes_body(self):
        self._test_create_group_type(bytes_body=True)

    def test_delete_group_type(self):
        self.check_service_client_function(
            self.client.delete_group_type,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            group_type_id='0e58433f-d108-4bf3-a22c-34e6b71ef86b',
            status=202)
