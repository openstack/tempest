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


class RolesClient(rest_client.RestClient):
    api_version = "v3"

    def create_role(self, **kwargs):
        """Create a Role.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#createRole
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.post('roles', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_roles(self):
        """Get the list of Roles."""
        resp, body = self.get("roles")
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_role(self, role_id, **kwargs):
        """Update a Role.

        Available params: see http://developer.openstack.org/
                          api-ref-identity-v3.html#updateRole
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.patch('roles/%s' % str(role_id), post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def assign_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def assign_user_role_on_domain(self, domain_id, user_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/users/%s/roles/%s' %
                              (domain_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_user_roles_on_project(self, project_id, user_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/users/%s/roles' %
                              (project_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_user_roles_on_domain(self, domain_id, user_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/users/%s/roles' %
                              (domain_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_user_on_project(self, project_id, user_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/users/%s/roles/%s' %
                                 (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_user_on_domain(self, domain_id, user_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/users/%s/roles/%s' %
                                 (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_user_role_existence_on_project(self, project_id,
                                             user_id, role_id):
        """Check role of a user on a project."""
        resp, body = self.head('projects/%s/users/%s/roles/%s' %
                               (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def check_user_role_existence_on_domain(self, domain_id,
                                            user_id, role_id):
        """Check role of a user on a domain."""
        resp, body = self.head('domains/%s/users/%s/roles/%s' %
                               (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def assign_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def assign_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_role_from_group_on_project_existence(self, project_id,
                                                   group_id, role_id):
        """Check role of a user on a project."""
        resp, body = self.head('projects/%s/groups/%s/roles/%s' %
                               (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def check_role_from_group_on_domain_existence(self, domain_id,
                                                  group_id, role_id):
        """Check role of a user on a domain."""
        resp, body = self.head('domains/%s/groups/%s/roles/%s' %
                               (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def assign_inherited_role_on_domains_user(
            self, domain_id, user_id, role_id):
        """Assigns a role to a user on projects owned by a domain."""
        resp, body = self.put(
            "OS-INHERIT/domains/%s/users/%s/roles/%s/inherited_to_projects"
            % (domain_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def revoke_inherited_role_from_user_on_domain(
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
        resp, body = self.head(
            "OS-INHERIT/domains/%s/users/%s/roles/%s/inherited_to_projects"
            % (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def assign_inherited_role_on_domains_group(
            self, domain_id, group_id, role_id):
        """Assigns a role to a group on projects owned by a domain."""
        resp, body = self.put(
            "OS-INHERIT/domains/%s/groups/%s/roles/%s/inherited_to_projects"
            % (domain_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def revoke_inherited_role_from_group_on_domain(
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
        resp, body = self.head(
            "OS-INHERIT/domains/%s/groups/%s/roles/%s/inherited_to_projects"
            % (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def assign_inherited_role_on_projects_user(
            self, project_id, user_id, role_id):
        """Assigns a role to a user on projects in a subtree."""
        resp, body = self.put(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def revoke_inherited_role_from_user_on_project(
            self, project_id, user_id, role_id):
        """Revokes an inherited role from a user on a project."""
        resp, body = self.delete(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_user_has_flag_on_inherited_to_project(
            self, project_id, user_id, role_id):
        """Checks whether a user has a role assignment"""
        """with the inherited_to_projects flag on a project."""
        resp, body = self.head(
            "OS-INHERIT/projects/%s/users/%s/roles/%s/inherited_to_projects"
            % (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def assign_inherited_role_on_projects_group(
            self, project_id, group_id, role_id):
        """Assigns a role to a group on projects in a subtree."""
        resp, body = self.put(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def revoke_inherited_role_from_group_on_project(
            self, project_id, group_id, role_id):
        """Revokes an inherited role from a group on a project."""
        resp, body = self.delete(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_group_has_flag_on_inherited_to_project(
            self, project_id, group_id, role_id):
        """Checks whether a group has a role assignment"""
        """with the inherited_to_projects flag on a project."""
        resp, body = self.head(
            "OS-INHERIT/projects/%s/groups/%s/roles/%s/inherited_to_projects"
            % (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
