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

    def delete_role(self, role_id):
        """Delete a role"""
        resp, body = self.delete('OS-KSADM/roles/%s' % role_id)
        return resp, body

    def list_roles(self):
        """Returns roles"""
        resp, body = self.get('OS-KSADM/roles')
        body = json.loads(body)
        return resp, body['roles']
