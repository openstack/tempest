# Copyright 2018 AT&T Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import project_tags_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestProjectTagsClient(base.BaseServiceTest):

    FAKE_PROJECT_ID = "0c4e939acacf4376bdcd1129f1a054ad"

    FAKE_PROJECT_TAG = "foo"

    FAKE_PROJECT_TAGS = ["foo", "bar"]

    def setUp(self):
        super(TestProjectTagsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = project_tags_client.ProjectTagsClient(fake_auth,
                                                            'identity',
                                                            'regionOne')

    def _test_update_project_tag(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_project_tag,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            project_id=self.FAKE_PROJECT_ID,
            tag=self.FAKE_PROJECT_TAG,
            status=201)

    def _test_list_project_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_project_tags,
            'tempest.lib.common.rest_client.RestClient.get',
            {"tags": self.FAKE_PROJECT_TAGS},
            bytes_body,
            project_id=self.FAKE_PROJECT_ID)

    def _test_update_all_project_tags(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_all_project_tags,
            'tempest.lib.common.rest_client.RestClient.put',
            {"tags": self.FAKE_PROJECT_TAGS},
            bytes_body,
            project_id=self.FAKE_PROJECT_ID,
            tags=self.FAKE_PROJECT_TAGS)

    def test_update_project_tag_with_str_body(self):
        self._test_update_project_tag()

    def test_update_project_tag_with_bytes_body(self):
        self._test_update_project_tag(bytes_body=True)

    def test_list_project_tags_with_str_body(self):
        self._test_list_project_tags()

    def test_list_project_tags_with_bytes_body(self):
        self._test_list_project_tags(bytes_body=True)

    def test_update_all_project_tags_with_str_body(self):
        self._test_update_all_project_tags()

    def test_update_all_project_tags_with_bytes_body(self):
        self._test_update_all_project_tags(bytes_body=True)

    def test_check_project_project_tag_existence(self):
        self.check_service_client_function(
            self.client.check_project_tag_existence,
            'tempest.lib.common.rest_client.RestClient.get',
            {},
            project_id=self.FAKE_PROJECT_ID,
            tag=self.FAKE_PROJECT_TAG,
            status=204)

    def test_delete_project_tag(self):
        self.check_service_client_function(
            self.client.delete_project_tag,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id=self.FAKE_PROJECT_ID,
            tag=self.FAKE_PROJECT_TAG,
            status=204)

    def test_delete_all_project_tags(self):
        self.check_service_client_function(
            self.client.delete_all_project_tags,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id=self.FAKE_PROJECT_ID,
            status=204)
