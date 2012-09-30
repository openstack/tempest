from tempest.common.rest_client import RestClient
from tempest import exceptions
import httplib2
import json


class AdminClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AdminClientJSON, self).__init__(config, username, password,
                                              auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def has_admin_extensions(self):
        """
        Returns True if the KSADM Admin Extensions are supported
        False otherwise
        """
        if hasattr(self, '_has_admin_extensions'):
            return self._has_admin_extensions
        resp, body = self.list_roles()
        self._has_admin_extensions = ('status' in resp and resp.status != 503)
        return self._has_admin_extensions

    def create_role(self, name):
        """Create a role"""
        post_body = {
            'name': name,
        }
        post_body = json.dumps({'role': post_body})
        resp, body = self.post('OS-KSADM/roles', post_body, self.headers)
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
            'enabled': kwargs.get('enabled', 'true'),
        }
        post_body = json.dumps({'tenant': post_body})
        resp, body = self.post('tenants', post_body, self.headers)
        body = json.loads(body)
        return resp, body['tenant']

    def delete_role(self, role_id):
        """Delete a role"""
        resp, body = self.delete('OS-KSADM/roles/%s' % str(role_id))
        return resp, body

    def list_user_roles(self, tenant_id, user_id):
        """Returns a list of roles assigned to a user for a tenant"""
        url = '/tenants/%s/users/%s/roles' % (tenant_id, user_id)
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['roles']

    def assign_user_role(self, tenant_id, user_id, role_id):
        """Add roles to a user on a tenant"""
        post_body = json.dumps({})
        resp, body = self.put('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                              (tenant_id, user_id, role_id), post_body,
                              self.headers)
        body = json.loads(body)
        return resp, body['role']

    def remove_user_role(self, tenant_id, user_id, role_id):
        """Removes a role assignment for a user on a tenant"""
        return self.delete('/tenants/%s/users/%s/roles/OS-KSADM/%s' %
                           (tenant_id, user_id, role_id))

    def delete_tenant(self, tenant_id):
        """Delete a tenant"""
        resp, body = self.delete('tenants/%s' % str(tenant_id))
        return resp, body

    def get_tenant(self, tenant_id):
        """Get tenant details"""
        resp, body = self.get('tenants/%s' % str(tenant_id))
        body = json.loads(body)
        return resp, body['tenant']

    def list_roles(self):
        """Returns roles"""
        resp, body = self.get('OS-KSADM/roles')
        body = json.loads(body)
        return resp, body['roles']

    def list_tenants(self):
        """Returns tenants"""
        resp, body = self.get('tenants')
        body = json.loads(body)
        return resp, body['tenants']

    def get_tenant_by_name(self, tenant_name):
        resp, tenants = self.list_tenants()
        for tenant in tenants:
            if tenant['name'] == tenant_name:
                return tenant
        raise exceptions.NotFound('No such tenant')

    def update_tenant(self, tenant_id, **kwargs):
        """Updates a tenant"""
        resp, body = self.get_tenant(tenant_id)
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
        resp, body = self.post('tenants/%s' % tenant_id, post_body,
                               self.headers)
        body = json.loads(body)
        return resp, body['tenant']

    def create_user(self, name, password, tenant_id, email):
        """Create a user"""
        post_body = {
            'name': name,
            'password': password,
            'tenantId': tenant_id,
            'email': email
        }
        post_body = json.dumps({'user': post_body})
        resp, body = self.post('users', post_body, self.headers)
        body = json.loads(body)
        return resp, body['user']

    def delete_user(self, user_id):
        """Delete a user"""
        resp, body = self.delete("users/%s" % user_id)
        return resp, body

    def get_users(self):
        """Get the list of users"""
        resp, body = self.get("users")
        body = json.loads(body)
        return resp, body['users']

    def enable_disable_user(self, user_id, enabled):
        """Enables or disables a user"""
        put_body = {
                'enabled': enabled
        }
        put_body = json.dumps({'user': put_body})
        resp, body = self.put('users/%s/enabled' % user_id,
                              put_body, self.headers)
        body = json.loads(body)
        return resp, body

    def delete_token(self, token_id):
        """Delete a token"""
        resp, body = self.delete("tokens/%s" % token_id)
        return resp, body

    def list_users_for_tenant(self, tenant_id):
        """List users for a Tenant"""
        resp, body = self.get('/tenants/%s/users' % tenant_id)
        body = json.loads(body)
        return resp, body['users']

    def get_user_by_username(self, tenant_id, username):
        resp, users = self.list_users_for_tenant(tenant_id)
        for user in users:
            if user['name'] == username:
                return user
        raise exceptions.NotFound('No such user')

    def create_service(self, name, type, **kwargs):
        """Create a service"""
        post_body = {
                      'name': name,
                      'type': type,
                      'description': kwargs.get('description')}
        post_body = json.dumps({'OS-KSADM:service': post_body})
        resp, body = self.post('/OS-KSADM/services', post_body, self.headers)
        body = json.loads(body)
        return resp, body['OS-KSADM:service']

    def get_service(self, service_id):
        """Get Service"""
        url = '/OS-KSADM/services/%s' % service_id
        resp, body = self.get(url)
        body = json.loads(body)
        return resp, body['OS-KSADM:service']

    def delete_service(self, service_id):
        """Delete Service"""
        url = '/OS-KSADM/services/%s' % service_id
        return self.delete(url)


class TokenClientJSON(RestClient):

    def __init__(self, config):
        self.auth_url = config.identity.auth_url

    def auth(self, user, password, tenant):
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user,
                    'password': password,
                },
                'tenantName': tenant,
            }
        }
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, headers=headers, body=body)
        return resp, body

    def request(self, method, url, headers=None, body=None):
        """A simple HTTP request interface."""
        self.http_obj = httplib2.Http()
        if headers is None:
            headers = {}

        resp, resp_body = self.http_obj.request(url, method,
                                                headers=headers, body=body)

        if resp.status in (401, 403):
            resp_body = json.loads(resp_body)
            raise exceptions.Unauthorized(resp_body['error']['message'])

        return resp, resp_body

    def get_token(self, user, password, tenant):
        resp, body = self.auth(user, password, tenant)
        if resp['status'] != '202':
            body = json.loads(body)
            access = body['access']
            token = access['token']
            return token['id']
