# Copyright 2016 EasyStack. All rights reserved.
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

from tempest.lib.services.image.v2 import namespace_tags_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNamespaceTagsClient(base.BaseServiceTest):
    FAKE_CREATE_SHOW_TAGS = {
        "created_at": "2015-05-09T01:12:31Z",
        "name": "added-sample-tag",
        "updated_at": "2015-05-09T01:12:31Z"
    }

    FAKE_LIST_TAGS = {
        "tags": [
            {
                "name": "sample-tag1"
            },
            {
                "name": "sample-tag2"
            },
            {
                "name": "sample-tag3"
            }
        ]
    }

    FAKE_UPDATE_TAGS = {"name": "new-tag-name"}

    def setUp(self):
        super(TestNamespaceTagsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = namespace_tags_client.NamespaceTagsClient(
            fake_auth, 'image', 'regionOne')

    def _test_create_namespace_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_namespace_tags,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SHOW_TAGS,
            bytes_body, status=201,
            namespace="OS::Compute::Hypervisor",
            tags=[{"name": "sample-tag1"},
                  {"name": "sample-tag2"},
                  {"name": "sample-tag3"}])

    def _test_list_namespace_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_namespace_tags,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_TAGS,
            bytes_body,
            namespace="OS::Compute::Hypervisor")

    def _test_create_namespace_tag_definition(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_namespace_tag,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_SHOW_TAGS,
            bytes_body,
            status=201,
            namespace="OS::Compute::Hypervisor",
            tag_name="added-sample-tag")

    def _test_show_namespace_tag_definition(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_namespace_tag,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_CREATE_SHOW_TAGS,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            tag_name="added-sample-tag")

    def _test_update_namespace_tag_definition(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_namespace_tag,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_OBJECTS,
            bytes_body,
            namespace="OS::Compute::Hypervisor",
            tag_name="added-sample-tag",
            name="new-tag-name")

    def test_create_namespace_tags_with_str_body(self):
        self._test_create_namespace_tags()

    def test_create_namespace_tags_with_bytes_body(self):
        self._test_create_namespace_tags(bytes_body=True)

    def test_list_namespace_tags_with_str_body(self):
        self._test_list_namespace_tags()

    def test_list_namespace_tags_with_bytes_body(self):
        self._test_list_namespace_tags(bytes_body=True)

    def test_create_namespace_tag_with_str_body(self):
        self._test_create_namespace_tag_definition()

    def test_create_namespace_tag_with_bytes_body(self):
        self._test_create_namespace_tag_definition(bytes_body=True)

    def test_show_namespace_tag_with_str_body(self):
        self._test_show_namespace_tag_definition()

    def test_show_namespace_tag_with_bytes_body(self):
        self._test_show_namespace_tag_definition(bytes_body=True)

    def test_delete_all_namespace_tags(self):
        self.check_service_client_function(
            self.client.delete_namespace_tags,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, status=200,
            namespace="OS::Compute::Hypervisor")
