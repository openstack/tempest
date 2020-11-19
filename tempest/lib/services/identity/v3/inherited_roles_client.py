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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class InheritedRolesClient(rest_client.RestClient):
    api_version = "v3"

    def create_inherited_role_on_domains_user(
            self, domain_id, user_id, role_id):
        """Assigns a role to a user on projects owned by a domain."""
        resp, body = self.put(
            "OS-INHERIT/domains/%s/users/%s/roles/%s/inherited_to_projects"
            % (domain_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_inherited_role_from_user_on_domain(
            self, domain_id, user_id, role_id):
        """Revokes an inherited project role from a user on a domain."""
        resp, body = self.delete(
            "OS-INHERIT/domains/%s/users/%s/roles/%s/inherited_to_projects"
            % (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_inherited_project_role_for_user_on_domain(
            self, domain_id, user_id):
        """Lists the inherited project roles on a domain for a user."""
        resp, body = self.get(
            "OS-INHERIT/domains/%s/users/%s/roles/inherited_to_projects"
            % (domain_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_user_inherited_project_role_on_domain(
            self, domain_id, user_id, role_id):
        """Checks whether a user has an inherited project role on a domain."""
        resp, _ = self.head(
            "OS-INHERIT/domains/%s/users/%s/roles/%s/inherited_to_projects"
            % (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def create_inherited_role_on_domains_group(
            self, domain_id, group_id, role_id):
        """Assigns a role to a group on projects owned by a domain."""
        resp, body = self.put(
            "OS-INHERIT/domains/%s/groups/%s/roles/%s/inherited_to_projects"
            % (domain_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_inherited_role_from_group_on_domain(
            self, domain_id, group_id, role_id):
        """Revokes an inherited project role from a group on a domain."""
        resp, body = self.delete(
            "OS-INHERIT/domains/%s/groups/%s/roles/%s/inherited_to_projects"
            % (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_inherited_project_role_for_group_on_domain(
            self, domain_id, group_id):
        """Lists the inherited project roles on a domain for a group."""
        resp, body = self.get(
            "OS-INHERIT/domains/%s/groups/%s/roles/inherited_to_projects"
            % (domain_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_group_inherited_project_role_on_domain(
            self, domain_id, group_id, role_id):
        """Checks whether a group has an inherited project role on a domain."""
        resp, _ = self.head(
            "OS-INHERIT/domains/%s/groups/%s/roles/%s/inherited_to_projects"
            % (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def create_inherited_role_on_projects_user(
            self, project_id, user_id, role_id):
        """Assigns a role to a user on projects in a subtree."""
        resp, body = self.put(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_inherited_role_from_user_on_project(
            self, project_id, user_id, role_id):
        """Revokes an inherited role from a user on a project."""
        resp, body = self.delete(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_user_has_flag_on_inherited_to_project(
            self, project_id, user_id, role_id):
        """Check if user has an inherited project role on project"""
        resp, _ = self.head(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def create_inherited_role_on_projects_group(
            self, project_id, group_id, role_id):
        """Assigns a role to a group on projects in a subtree."""
        resp, body = self.put(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_inherited_role_from_group_on_project(
            self, project_id, group_id, role_id):
        """Revokes an inherited role from a group on a project."""
        resp, body = self.delete(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_group_has_flag_on_inherited_to_project(
            self, project_id, group_id, role_id):
        """Check if group has an inherited project role on project"""
        resp, _ = self.head(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
