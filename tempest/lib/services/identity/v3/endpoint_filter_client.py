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

"""
https://docs.openstack.org/api-ref/identity/v3-ext/#os-ep-filter-api
"""

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class EndPointsFilterClient(rest_client.RestClient):
    api_version = "v3"
    ep_filter = "OS-EP-FILTER"

    def list_projects_for_endpoint(self, endpoint_id):
        """List all projects that are associated with the endpoint."""
        resp, body = self.get(self.ep_filter + '/endpoints/%s/projects' %
                              endpoint_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def add_endpoint_to_project(self, project_id, endpoint_id):
        """Add association between project and endpoint. """
        body = None
        resp, body = self.put(
            self.ep_filter + '/projects/%s/endpoints/%s' %
            (project_id, endpoint_id), body)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_endpoint_in_project(self, project_id, endpoint_id):
        """Check association of Project with Endpoint."""
        resp, body = self.head(
            self.ep_filter + '/projects/%s/endpoints/%s' %
            (project_id, endpoint_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_endpoints_in_project(self, project_id):
        """List Endpoints associated with Project."""
        resp, body = self.get(self.ep_filter + '/projects/%s/endpoints'
                              % project_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_endpoint_from_project(self, project_id, endpoint_id):
        """Delete association between project and endpoint."""
        resp, body = self.delete(
            self.ep_filter + '/projects/%s/endpoints/%s'
            % (project_id, endpoint_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_endpoint_groups_for_project(self, project_id):
        """List Endpoint Groups Associated with Project."""
        resp, body = self.get(
            self.ep_filter + '/projects/%s/endpoint_groups'
            % project_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_projects_for_endpoint_group(self, endpoint_group_id):
        """List Projects Associated with Endpoint Group."""
        resp, body = self.get(
            self.ep_filter + '/endpoint_groups/%s/projects'
            % endpoint_group_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_endpoints_for_endpoint_group(self, endpoint_group_id):
        """List Endpoints Associated with Endpoint Group."""
        resp, body = self.get(
            self.ep_filter + '/endpoint_groups/%s/endpoints'
            % endpoint_group_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def add_endpoint_group_to_project(self, endpoint_group_id, project_id):
        """Create Endpoint Group to Project Association."""
        body = None
        resp, body = self.put(
            self.ep_filter + '/endpoint_groups/%s/projects/%s'
            % (endpoint_group_id, project_id), body)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_endpoint_group_for_project(self, endpoint_group_id, project_id):
        """Get Endpoint Group to Project Association."""
        resp, body = self.get(
            self.ep_filter + '/endpoint_groups/%s/projects/%s'
            % (endpoint_group_id, project_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_endpoint_group_from_project(
        self, endpoint_group_id, project_id):
        """Delete Endpoint Group to Project Association."""
        resp, body = self.delete(
            self.ep_filter + '/endpoint_groups/%s/projects/%s'
            % (endpoint_group_id, project_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
