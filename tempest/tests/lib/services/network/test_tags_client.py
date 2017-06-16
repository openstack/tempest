# Copyright 2017 AT&T Corporation.
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


from tempest.lib.services.network import tags_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTagsClient(base.BaseServiceTest):

    FAKE_TAGS = {
        "tags": [
            "red",
            "blue"
        ]
    }

    FAKE_RESOURCE_TYPE = 'network'

    FAKE_RESOURCE_ID = '7a8f904b-c1ed-4446-a87d-60440c02934b'

    def setUp(self):
        super(TestTagsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = tags_client.TagsClient(
            fake_auth, 'network', 'regionOne')

    def _test_update_all_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_all_tags,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_TAGS,
            bytes_body,
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID,
            tags=self.FAKE_TAGS)

    def _test_check_tag_existence(self, bytes_body=False):
        self.check_service_client_function(
            self.client.check_tag_existence,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            bytes_body,
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID,
            tag=self.FAKE_TAGS['tags'][0],
            status=204)

    def _test_create_tag(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_tag,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID,
            tag=self.FAKE_TAGS['tags'][0],
            status=201)

    def _test_list_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_tags,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_TAGS,
            bytes_body,
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID)

    def test_update_all_tags_with_str_body(self):
        self._test_update_all_tags()

    def test_update_all_tags_with_bytes_body(self):
        self._test_update_all_tags(bytes_body=True)

    def test_delete_all_tags(self):
        self.check_service_client_function(
            self.client.delete_all_tags,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID,
            status=204)

    def test_check_tag_existence_with_str_body(self):
        self._test_check_tag_existence()

    def test_check_tag_existence_with_bytes_body(self):
        self._test_check_tag_existence(bytes_body=True)

    def test_create_tag_with_str_body(self):
        self._test_create_tag()

    def test_create_tag_with_bytes_body(self):
        self._test_create_tag(bytes_body=True)

    def test_list_tags_with_str_body(self):
        self._test_list_tags()

    def test_list_tags_with_bytes_body(self):
        self._test_list_tags(bytes_body=True)

    def test_delete_tag(self):
        self.check_service_client_function(
            self.client.delete_tag,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            resource_type=self.FAKE_RESOURCE_TYPE,
            resource_id=self.FAKE_RESOURCE_ID,
            tag=self.FAKE_TAGS['tags'][0],
            status=204)
