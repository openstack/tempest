# Copyright 2017 AT&T Corp.
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

from tempest.lib.services.identity.v3 import endpoint_filter_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestEndPointsFilterClient(base.BaseServiceTest):
    FAKE_LIST_PROJECTS_FOR_ENDPOINTS = {
        "projects": [
            {
                "domain_id": "1777c7",
                "enabled": True,
                "id": "1234ab1",
                "type": "compute",
                "links": {
                    "self": "http://example.com/identity/v3/projects/1234ab1"
                },
                "name": "Project 1",
                "description": "Project 1 description",
            },
            {
                "domain_id": "1777c7",
                "enabled": True,
                "id": "5678cd2",
                "type": "compute",
                "links": {
                    "self": "http://example.com/identity/v3/projects/5678cd2"
                },
                "name": "Project 2",
                "description": "Project 2 description",
            }
        ],
        "links": {
            "self": "http://example.com/identity/v3/OS-EP-FILTER/endpoints/\
                    u6ay5u/projects",
            "previous": None,
            "next": None
        }
    }

    FAKE_LIST_ENDPOINTS_FOR_PROJECTS = {
        "endpoints": [
            {
                "id": "u6ay5u",
                "interface": "public",
                "url": "http://example.com/identity/",
                "region": "north",
                "links": {
                    "self": "http://example.com/identity/v3/endpoints/u6ay5u"
                },
                "service_id": "5um4r",
            },
            {
                "id": "u6ay5u",
                "interface": "internal",
                "url": "http://example.com/identity/",
                "region": "south",
                "links": {
                    "self": "http://example.com/identity/v3/endpoints/u6ay5u"
                },
                "service_id": "5um4r",
            },
        ],
        "links": {
            "self": "http://example.com/identity/v3/OS-EP-FILTER/projects/\
                    1234ab1/endpoints",
            "previous": None,
            "next": None
        }
    }

    FAKE_LIST_ENDPOINT_GROUPS_FOR_PROJECT = {
        "endpoint_groups": [
            {
                "endpoint_group": {
                    "description": "endpoint group description #2",
                    "filters": {
                        "interface": "admin"
                    },
                    "id": "3de68c",
                    "name": "endpoint group name #2"
                }
            }
            ],
        "links": {
            "self": "https://url/identity/v3/OS-EP-FILTER/endpoint_groups",
        }
    }

    FAKE_PROJECT_INFO = {
        "project": {
            "domain_id": "1789d1",
            "id": "263fd9",
            "links": {
                "self": "http://example.com/identity/v3/projects/263fd9"
            },
            "name": "project name #1",
            "description": "project description #1"
        }
    }

    def setUp(self):
        super(TestEndPointsFilterClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = endpoint_filter_client.EndPointsFilterClient(
            fake_auth, 'identity', 'regionOne')

    def _test_add_endpoint_to_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.add_endpoint_to_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            status=204,
            project_id=3,
            endpoint_id=4)

    def _test_check_endpoint_in_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.check_endpoint_in_project,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            bytes_body,
            status=204,
            project_id=3,
            endpoint_id=4)

    def _test_list_projects_for_endpoint(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_projects_for_endpoint,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_PROJECTS_FOR_ENDPOINTS,
            bytes_body,
            status=200,
            endpoint_id=3)

    def _test_list_endpoints_in_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoints_in_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ENDPOINTS_FOR_PROJECTS,
            bytes_body,
            status=200,
            project_id=4)

    def _test_delete_endpoint_from_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_endpoint_from_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            bytes_body,
            status=204,
            project_id=3,
            endpoint_id=4)

    def _test_list_endpoint_groups_for_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoint_groups_for_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ENDPOINT_GROUPS_FOR_PROJECT,
            bytes_body,
            status=200,
            project_id=3)

    def _test_list_projects_for_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_projects_for_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_PROJECTS_FOR_ENDPOINTS,
            bytes_body,
            status=200,
            endpoint_group_id=5)

    def _test_list_endpoints_for_endpoint_group(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_endpoints_for_endpoint_group,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ENDPOINTS_FOR_PROJECTS,
            bytes_body,
            status=200,
            endpoint_group_id=5)

    def _test_add_endpoint_group_to_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.add_endpoint_group_to_project,
            'tempest.lib.common.rest_client.RestClient.put',
            {},
            bytes_body,
            status=204,
            endpoint_group_id=5,
            project_id=6)

    def _test_show_endpoint_group_for_project(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_endpoint_group_for_project,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_PROJECT_INFO,
            bytes_body,
            endpoint_group_id=5,
            project_id=6)

    def test_add_endpoint_to_project_with_str_body(self):
        self._test_add_endpoint_to_project()

    def test_add_endpoint_to_project_with_bytes_body(self):
        self._test_add_endpoint_to_project(bytes_body=True)

    def test_check_endpoint_in_project_with_str_body(self):
        self._test_check_endpoint_in_project()

    def test_check_endpoint_in_project_with_bytes_body(self):
        self._test_check_endpoint_in_project(bytes_body=True)

    def test_list_projects_for_endpoint_with_str_body(self):
        self._test_list_projects_for_endpoint()

    def test_list_projects_for_endpoint_with_bytes_body(self):
        self._test_list_projects_for_endpoint(bytes_body=True)

    def test_list_endpoints_in_project_with_str_body(self):
        self._test_list_endpoints_in_project()

    def test_list_endpoints_in_project_with_bytes_body(self):
        self._test_list_endpoints_in_project(bytes_body=True)

    def test_delete_endpoint_from_project(self):
        self._test_delete_endpoint_from_project()

    def test_list_endpoint_groups_for_project_with_str_body(self):
        self._test_list_endpoint_groups_for_project()

    def test_list_endpoint_groups_for_project_with_bytes_body(self):
        self._test_list_endpoint_groups_for_project(bytes_body=True)

    def test_list_projects_for_endpoint_group_with_str_body(self):
        self._test_list_projects_for_endpoint_group()

    def test_list_projects_for_endpoint_group_with_bytes_body(self):
        self._test_list_projects_for_endpoint_group(bytes_body=True)

    def test_list_endpoints_for_endpoint_group_with_str_body(self):
        self._test_list_endpoints_for_endpoint_group()

    def test_list_endpoints_for_endpoint_group_with_bytes_body(self):
        self._test_list_endpoints_for_endpoint_group(bytes_body=True)

    def test_add_endpoint_group_to_project_with_str_body(self):
        self._test_add_endpoint_group_to_project()

    def test_add_endpoint_group_to_project_with_bytes_body(self):
        self._test_add_endpoint_group_to_project(bytes_body=True)

    def test_show_endpoint_group_for_project_with_str_body(self):
        self._test_show_endpoint_group_for_project()

    def test_show_endpoint_group_for_project_with_bytes_body(self):
        self._test_show_endpoint_group_for_project(bytes_body=True)

    def test_delete_endpoint_group_from_project(self):
        self.check_service_client_function(
            self.client.delete_endpoint_group_from_project,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            False,
            status=204,
            endpoint_group_id=5,
            project_id=5)
