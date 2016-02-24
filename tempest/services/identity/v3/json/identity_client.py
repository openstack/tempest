# Copyright 2013 OpenStack Foundation
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

from oslo_serialization import jsonutils as json

from tempest.common import service_client


class IdentityV3Client(service_client.ServiceClient):
    api_version = "v3"

    def show_api_description(self):
        """Retrieves info about the v3 Identity API"""
        url = ''
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def create_role(self, **kwargs):
        """Create a Role.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#createRole
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.post('roles', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_roles(self):
        """Get the list of Roles."""
        resp, body = self.get("roles")
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def update_role(self, role_id, **kwargs):
        """Update a Role.

        Available params: see http://developer.openstack.org/
                          api-ref-identity-v3.html#updateRole
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.patch('roles/%s' % str(role_id), post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def show_token(self, resp_token):
        """Get token details."""
        headers = {'X-Subject-Token': resp_token}
        resp, body = self.get("auth/tokens", headers=headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_token(self, resp_token):
        """Deletes token."""
        headers = {'X-Subject-Token': resp_token}
        resp, body = self.delete("auth/tokens", headers=headers)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def assign_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def assign_user_role_on_domain(self, domain_id, user_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/users/%s/roles/%s' %
                              (domain_id, user_id, role_id), None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_user_roles_on_project(self, project_id, user_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/users/%s/roles' %
                              (project_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_user_roles_on_domain(self, domain_id, user_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/users/%s/roles' %
                              (domain_id, user_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_role_from_user_on_project(self, project_id, user_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/users/%s/roles/%s' %
                                 (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def delete_role_from_user_on_domain(self, domain_id, user_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/users/%s/roles/%s' %
                                 (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def check_user_role_existence_on_project(self, project_id,
                                             user_id, role_id):
        """Check role of a user on a project."""
        resp, body = self.head('projects/%s/users/%s/roles/%s' %
                               (project_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def check_user_role_existence_on_domain(self, domain_id,
                                            user_id, role_id):
        """Check role of a user on a domain."""
        resp, body = self.head('domains/%s/users/%s/roles/%s' %
                               (domain_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def assign_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def assign_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def delete_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def check_role_from_group_on_project_existence(self, project_id,
                                                   group_id, role_id):
        """Check role of a user on a project."""
        resp, body = self.head('projects/%s/groups/%s/roles/%s' %
                               (project_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def check_role_from_group_on_domain_existence(self, domain_id,
                                                  group_id, role_id):
        """Check role of a user on a domain."""
        resp, body = self.head('domains/%s/groups/%s/roles/%s' %
                               (domain_id, group_id, role_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp)

    def create_trust(self, **kwargs):
        """Creates a trust.

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3-ext.html#createTrust
        """
        post_body = json.dumps({'trust': kwargs})
        resp, body = self.post('OS-TRUST/trusts', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_trust(self, trust_id):
        """Deletes a trust."""
        resp, body = self.delete("OS-TRUST/trusts/%s" % trust_id)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_trusts(self, trustor_user_id=None, trustee_user_id=None):
        """GET trusts."""
        if trustor_user_id:
            resp, body = self.get("OS-TRUST/trusts?trustor_user_id=%s"
                                  % trustor_user_id)
        elif trustee_user_id:
            resp, body = self.get("OS-TRUST/trusts?trustee_user_id=%s"
                                  % trustee_user_id)
        else:
            resp, body = self.get("OS-TRUST/trusts")
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_trust(self, trust_id):
        """GET trust."""
        resp, body = self.get("OS-TRUST/trusts/%s" % trust_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_trust_roles(self, trust_id):
        """GET roles delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles" % trust_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def show_trust_role(self, trust_id, role_id):
        """GET role delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles/%s"
                              % (trust_id, role_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def check_trust_role(self, trust_id, role_id):
        """HEAD Check if role is delegated by a trust."""
        resp, body = self.head("OS-TRUST/trusts/%s/roles/%s"
                               % (trust_id, role_id))
        self.expected_success(200, resp.status)
        return service_client.ResponseBody(resp, body)
