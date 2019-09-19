# Copyright 2016 Red Hat, Inc.
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

from tempest.lib.services.identity.v3 import projects_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestProjectsClient(base.BaseServiceTest):
    FAKE_CREATE_PROJECT = {
        "project": {
            "description": "My new project",
            "domain_id": "default",
            "enabled": True,
            "is_domain": False,
            "name": "myNewProject"
        }
    }

    FAKE_PROJECT_INFO = {
        "project": {
            "is_domain": False,
            "description": None,
            "domain_id": "default",
            "enabled": True,
            "id": "0c4e939acacf4376bdcd1129f1a054ad",
            "links": {
                "self": "http://example.com/identity/v3/projects/0c4e" +
                        "939acacf4376bdcd1129f1a054ad"
            },
            "name": "admin",
            "parent_id": "default"
        }
    }

    FAKE_LIST_PROJECTS = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/projects"
        },
        "projects": [
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "0c4e939acacf4376bdcd1129f1a054ad",
                "links": {
                    "self": "http://example.com/identity/v3/projects" +
                            "/0c4e939acacf4376bdcd1129f1a054ad"
                },
                "name": "admin",
                "parent_id": None,
                "tags": []
            },
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "0cbd49cbf76d405d9c86562e1d579bd3",
                "links": {
                    "self": "http://example.com/identity/v3/projects" +
                            "/0cbd49cbf76d405d9c86562e1d579bd3"
                },
                "name": "demo",
                "parent_id": None,
                "tags": []
            },
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "2db68fed84324f29bb73130c6c2094fb",
                "links": {
                    "self": "http://example.com/identity/v3/projects" +
                            "/2db68fed84324f29bb73130c6c2094fb"
                },
                "name": "swifttenanttest2",
                "parent_id": None,
                "tags": []
            },
            {
                "is_domain": False,
                "description": None,
                "domain_id": "default",
                "enabled": True,
                "id": "3d594eb0f04741069dbbb521635b21c7",
                "links": {
                    "self": "http://example.com/identity/v3/projects" +
                            "/3d594eb0f04741069dbbb521635b21c7"
                },
                "name": "service",
                "parent_id": None,
                "tags": []
            }
        ]
    }

    def setUp(self):
        super(TestProjectsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = projects_client.ProjectsClient(fake_auth,
                                                     'identity',
                                                     'regionOne')

    def _test_create_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_project,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_PROJECT,
            bytes_body,
            name=self.FAKE_CREATE_PROJECT["project"]["name"],
            status=201)

    def _test_show_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_PROJECT_INFO,
            bytes_body,
            project_id="0c4e939acacf4376bdcd1129f1a054ad")

    def _test_list_projects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_projects,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_PROJECTS,
            bytes_body)

    def _test_update_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_project,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_PROJECT_INFO,
            bytes_body,
            project_id="0c4e939acacf4376bdcd1129f1a054ad")

    def test_create_project_with_str_body(self):
        self._test_create_project()

    def test_create_project_with_bytes_body(self):
        self._test_create_project(bytes_body=True)

    def test_show_project_with_str_body(self):
        self._test_show_project()

    def test_show_project_with_bytes_body(self):
        self._test_show_project(bytes_body=True)

    def test_list_projects_with_str_body(self):
        self._test_list_projects()

    def test_list_projects_with_bytes_body(self):
        self._test_list_projects(bytes_body=True)

    def test_update_project_with_str_body(self):
        self._test_update_project()

    def test_update_project_with_bytes_body(self):
        self._test_update_project(bytes_body=True)

    def test_delete_project(self):
        self.check_service_client_function(
            self.client.delete_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            project_id="0c4e939acacf4376bdcd1129f1a054ad",
            status=204)
