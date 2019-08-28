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
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client


class RolesClient(rest_client.RestClient):
    api_version = "v3"

    def create_role(self, **kwargs):
        """Create a Role.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#create-role
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.post('roles', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % role_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_roles(self, **params):
        """Get the list of Roles.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#list-roles
        """
        url = 'roles'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_role(self, role_id, **kwargs):
        """Update a Role.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#update-role
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.patch('roles/%s' % role_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % role_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_user_role_on_domain(self, domain_id, user_id, role_id):
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

    def create_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a group on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a group on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a group on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a group on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a group on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a group on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def check_role_from_group_on_project_existence(self, project_id,
                                                   group_id, role_id):
        """Check role of a group on a project."""
        resp, body = self.head('projects/%s/groups/%s/roles/%s' %
                               (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def check_role_from_group_on_domain_existence(self, domain_id,
                                                  group_id, role_id):
        """Check role of a group on a domain."""
        resp, body = self.head('domains/%s/groups/%s/roles/%s' %
                               (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def create_role_inference_rule(self, prior_role, implies_role):
        """Create a role inference rule."""
        resp, body = self.put('roles/%s/implies/%s' %
                              (prior_role, implies_role), None)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_role_inference_rule(self, prior_role, implies_role):
        """Get a role inference rule."""
        resp, body = self.get('roles/%s/implies/%s' %
                              (prior_role, implies_role))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_role_inferences_rules(self, prior_role):
        """List the inferences rules from a role."""
        resp, body = self.get('roles/%s/implies' % prior_role)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_all_role_inference_rules(self):
        """Lists all role inference rules.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#list-all-role-inference-rules
        """
        resp, body = self.get('role_inferences')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def check_role_inference_rule(self, prior_role, implies_role):
        """Check a role inference rule."""
        resp, body = self.head('roles/%s/implies/%s' %
                               (prior_role, implies_role))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def delete_role_inference_rule(self, prior_role, implies_role):
        """Delete a role inference rule."""
        resp, body = self.delete('roles/%s/implies/%s' %
                                 (prior_role, implies_role))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)
