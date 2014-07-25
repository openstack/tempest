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

import json

from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class IdentityClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(IdentityClientJSON, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'

        # Needed for xml service client
        self.list_tags = ["roles", "tenants", "users", "services",
                          "extensions"]

    def has_admin_extensions(self):
        """
        Returns True if the KSADM Admin Extensions are supported
        False otherwise
        """
        if hasattr(self, '_has_admin_extensions'):
            return self._has_admin_extensions
        # Try something that requires admin
        try:
            self.list_roles()
            self._has_admin_extensions = True
        except Exception:
            self._has_admin_extensions = False
        return self._has_admin_extensions

    def create_role(self, name):
        """Create a role."""
        post_body = {
            'name': name,
        }
        post_body = json.dumps({'role': post_body})
        resp, body = self.post('OS-KSADM/roles', post_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_role(self, role_id):
        """Get a role by its id."""
        resp, body = self.get('OS-KSADM/roles/%s' % role_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['role']

    def create_tenant(self, name, **kwargs):
        """
        Create a tenant
        name (required): New tenant name
        description: Description of new tenant (default is none)
        enabled <true|false>: Initial tenant status (default is true)
        """
        post_body = {
            'name': name,
            'description': kwargs.get('description', ''),
            'enabled': kwargs.get('enabled', True),
        }
        post_body = json.dumps({'tenant': post_body})
        resp, body = self.post('tenants', post_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('OS-KSADM/roles/%s' % str(role_id))
        self.expected_success(204, resp.status)
        return resp, body

    def list_user_roles(self, tenant_id, user_id):
        """Returns a list of roles assigned to a user for a tenant."""
        url = '/tenants/%s/users/%s/roles' % (tenant_id, user_id)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def assign_user_role(self, tenant_id, user_id, role_id):
        """Add roles to a user on a tenant."""
        resp, body = self.put('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                              (tenant_id, user_id, role_id), "")
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def remove_user_role(self, tenant_id, user_id, role_id):
        """Removes a role assignment for a user on a tenant."""
        resp, body = self.delete('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                                 (tenant_id, user_id, role_id))
        self.expected_success(204, resp.status)
        return resp, body

    def delete_tenant(self, tenant_id):
        """Delete a tenant."""
        resp, body = self.delete('tenants/%s' % str(tenant_id))
        self.expected_success(204, resp.status)
        return resp, body

    def get_tenant(self, tenant_id):
        """Get tenant details."""
        resp, body = self.get('tenants/%s' % str(tenant_id))
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_roles(self):
        """Returns roles."""
        resp, body = self.get('OS-KSADM/roles')
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_tenants(self):
        """Returns tenants."""
        resp, body = self.get('tenants')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['tenants']

    def get_tenant_by_name(self, tenant_name):
        _, tenants = self.list_tenants()
        for tenant in tenants:
            if tenant['name'] == tenant_name:
                return tenant
        raise exceptions.NotFound('No such tenant')

    def update_tenant(self, tenant_id, **kwargs):
        """Updates a tenant."""
        _, body = self.get_tenant(tenant_id)
        name = kwargs.get('name', body['name'])
        desc = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        post_body = {
            'id': tenant_id,
            'name': name,
            'description': desc,
            'enabled': en,
        }
        post_body = json.dumps({'tenant': post_body})
        resp, body = self.post('tenants/%s' % tenant_id, post_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def create_user(self, name, password, tenant_id, email, **kwargs):
        """Create a user."""
        post_body = {
            'name': name,
            'password': password,
            'email': email
        }
        if tenant_id is not None:
            post_body['tenantId'] = tenant_id
        if kwargs.get('enabled') is not None:
            post_body['enabled'] = kwargs.get('enabled')
        post_body = json.dumps({'user': post_body})
        resp, body = self.post('users', post_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def update_user(self, user_id, **kwargs):
        """Updates a user."""
        put_body = json.dumps({'user': kwargs})
        resp, body = self.put('users/%s' % user_id, put_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_user(self, user_id):
        """GET a user."""
        resp, body = self.get("users/%s" % user_id)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def delete_user(self, user_id):
        """Delete a user."""
        resp, body = self.delete("users/%s" % user_id)
        self.expected_success(204, resp.status)
        return resp, body

    def get_users(self):
        """Get the list of users."""
        resp, body = self.get("users")
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def enable_disable_user(self, user_id, enabled):
        """Enables or disables a user."""
        put_body = {
            'enabled': enabled
        }
        put_body = json.dumps({'user': put_body})
        resp, body = self.put('users/%s/enabled' % user_id, put_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_token(self, token_id):
        """Get token details."""
        resp, body = self.get("tokens/%s" % token_id)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def delete_token(self, token_id):
        """Delete a token."""
        resp, body = self.delete("tokens/%s" % token_id)
        self.expected_success(204, resp.status)
        return resp, body

    def list_users_for_tenant(self, tenant_id):
        """List users for a Tenant."""
        resp, body = self.get('/tenants/%s/users' % tenant_id)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_user_by_username(self, tenant_id, username):
        _, users = self.list_users_for_tenant(tenant_id)
        for user in users:
            if user['name'] == username:
                return user
        raise exceptions.NotFound('No such user')

    def create_service(self, name, type, **kwargs):
        """Create a service."""
        post_body = {
            'name': name,
            'type': type,
            'description': kwargs.get('description')
        }
        post_body = json.dumps({'OS-KSADM:service': post_body})
        resp, body = self.post('/OS-KSADM/services', post_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def get_service(self, service_id):
        """Get Service."""
        url = '/OS-KSADM/services/%s' % service_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_services(self):
        """List Service - Returns Services."""
        resp, body = self.get('/OS-KSADM/services')
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def delete_service(self, service_id):
        """Delete Service."""
        url = '/OS-KSADM/services/%s' % service_id
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
        return resp, body

    def update_user_password(self, user_id, new_pass):
        """Update User Password."""
        put_body = {
            'password': new_pass,
            'id': user_id
        }
        put_body = json.dumps({'user': put_body})
        resp, body = self.put('users/%s/OS-KSADM/password' % user_id, put_body)
        self.expected_success(200, resp.status)
        return resp, self._parse_resp(body)

    def list_extensions(self):
        """List all the extensions."""
        resp, body = self.get('/extensions')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['extensions']['values']


class TokenClientJSON(IdentityClientJSON):

    def __init__(self):
        super(TokenClientJSON, self).__init__(None)
        auth_url = CONF.identity.uri

        # Normalize URI to ensure /tokens is in it.
        if 'tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/tokens'

        self.auth_url = auth_url

    def auth(self, user, password, tenant=None):
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                },
            }
        }

        if tenant:
            creds['auth']['tenantName'] = tenant

        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, body=body)

        return resp, body['access']

    def auth_token(self, token_id, tenant=None):
        creds = {
            'auth': {
                'token': {
                    'id': token_id,
                },
            }
        }

        if tenant:
            creds['auth']['tenantName'] = tenant

        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, body=body)

        return resp, body['access']

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        """A simple HTTP request interface."""
        if headers is None:
            # Always accept 'json', for TokenClientXML too.
            # Because XML response is not easily
            # converted to the corresponding JSON one
            headers = self.get_headers(accept_type="json")
        elif extra_headers:
            try:
                headers.update(self.get_headers(accept_type="json"))
            except (ValueError, TypeError):
                headers = self.get_headers(accept_type="json")

        resp, resp_body = self.http_obj.request(url, method,
                                                headers=headers, body=body)
        self._log_request(method, url, resp)

        if resp.status in [401, 403]:
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])
        elif resp.status not in [200, 201]:
            raise exceptions.IdentityError(
                'Unexpected status code {0}'.format(resp.status))

        if isinstance(resp_body, str):
            resp_body = json.loads(resp_body)
        return resp, resp_body

    def get_token(self, user, password, tenant, auth_data=False):
        """
        Returns (token id, token data) for supplied credentials
        """
        resp, body = self.auth(user, password, tenant)

        if auth_data:
            return body['token']['id'], body
        else:
            return body['token']['id']
