from tempest.common.rest_client import RestClient
import json


class AdminClient(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(AdminClient, self).__init__(config, username, password,
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
        resp, body = self.post('OS-KSADM/roles', post_body,
                                      self.headers)
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
        resp, body = self.post('tenants', post_body,
                                      self.headers)
        body = json.loads(body)
        return resp, body['tenant']

    def delete_role(self, role_id):
        """Delete a role"""
        resp, body = self.delete('OS-KSADM/roles/%s' % str(role_id))
        return resp, body

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
