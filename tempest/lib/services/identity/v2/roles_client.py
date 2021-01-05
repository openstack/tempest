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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class RolesClient(rest_client.RestClient):
    api_version = "v2.0"

    def create_role(self, **kwargs):
        """Create a role.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#create-a-role
        """
        post_body = json.dumps({'role': kwargs})
        resp, body = self.post('OS-KSADM/roles', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_role(self, role_id_or_name):
        """Get a role by its id or name.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#show-a-role
        OR
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#show-role-information-by-name
        """
        resp, body = self.get('OS-KSADM/roles/%s' % role_id_or_name)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_roles(self, **params):
        """Returns roles.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#list-all-roles
        """
        url = 'OS-KSADM/roles'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role(self, role_id):
        """Delete a role.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#delete-a-role
        """
        resp, body = self.delete('OS-KSADM/roles/%s' % role_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_user_role_on_project(self, tenant_id, user_id, role_id):
        """Add roles to a user on a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#grant-roles-to-user-on-tenant
        """
        resp, body = self.put('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                              (tenant_id, user_id, role_id), "")
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_user_roles_on_project(self, tenant_id, user_id, **params):
        """Returns a list of roles assigned to a user for a tenant."""
        # TODO(gmann): Need to write API-ref link, Bug# 1592711
        url = '/tenants/%s/users/%s/roles' % (tenant_id, user_id)
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_role_from_user_on_project(self, tenant_id, user_id, role_id):
        """Removes a role assignment for a user on a tenant.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#revoke-role-from-user-on-tenant
        """
        resp, body = self.delete('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                                 (tenant_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)
