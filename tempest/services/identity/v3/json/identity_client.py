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

import json

from tempest.common import rest_client
from tempest import config
from tempest import exceptions

CONF = config.CONF


class IdentityV3ClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(IdentityV3ClientJSON, self).__init__(auth_provider)
        self.service = CONF.identity.catalog_type
        self.endpoint_url = 'adminURL'
        self.api_version = "v3"

    def create_user(self, user_name, **kwargs):
        """Creates a user."""
        password = kwargs.get('password', None)
        email = kwargs.get('email', None)
        en = kwargs.get('enabled', True)
        project_id = kwargs.get('project_id', None)
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
        post_body = {
            'project_id': project_id,
            'description': description,
            'domain_id': domain_id,
            'email': email,
            'enabled': en,
            'name': user_name,
            'password': password
        }
        post_body = json.dumps({'user': post_body})
        resp, body = self.post('users', post_body)
        body = json.loads(body)
        return resp, body['user']

    def update_user(self, user_id, name, **kwargs):
        """Updates a user."""
        resp, body = self.get_user(user_id)
        email = kwargs.get('email', body['email'])
        en = kwargs.get('enabled', body['enabled'])
        project_id = kwargs.get('project_id', body['project_id'])
        description = kwargs.get('description', body['description'])
        domain_id = kwargs.get('domain_id', body['domain_id'])
        post_body = {
            'name': name,
            'email': email,
            'enabled': en,
            'project_id': project_id,
            'id': user_id,
            'domain_id': domain_id,
            'description': description
        }
        post_body = json.dumps({'user': post_body})
        resp, body = self.patch('users/%s' % user_id, post_body)
        body = json.loads(body)
        return resp, body['user']

    def list_user_projects(self, user_id):
        """Lists the projects on which a user has roles assigned."""
        resp, body = self.get('users/%s/projects' % user_id)
        body = json.loads(body)
        return resp, body['projects']

    def get_users(self):
        """Get the list of users."""
        resp, body = self.get("users")
        body = json.loads(body)
        return resp, body['users']

    def get_user(self, user_id):
        """GET a user."""
        resp, body = self.get("users/%s" % user_id)
        body = json.loads(body)
        return resp, body['user']

    def delete_user(self, user_id):
        """Deletes a User."""
        resp, body = self.delete("users/%s" % user_id)
        return resp, body

    def create_project(self, name, **kwargs):
        """Creates a project."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', True)
        domain_id = kwargs.get('domain_id', 'default')
        post_body = {
            'description': description,
            'domain_id': domain_id,
            'enabled': en,
            'name': name
        }
        post_body = json.dumps({'project': post_body})
        resp, body = self.post('projects', post_body)
        body = json.loads(body)
        return resp, body['project']

    def list_projects(self):
        resp, body = self.get("projects")
        body = json.loads(body)
        return resp, body['projects']

    def update_project(self, project_id, **kwargs):
        resp, body = self.get_project(project_id)
        name = kwargs.get('name', body['name'])
        desc = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        domain_id = kwargs.get('domain_id', body['domain_id'])
        post_body = {
            'id': project_id,
            'name': name,
            'description': desc,
            'enabled': en,
            'domain_id': domain_id,
        }
        post_body = json.dumps({'project': post_body})
        resp, body = self.patch('projects/%s' % project_id, post_body)
        body = json.loads(body)
        return resp, body['project']

    def get_project(self, project_id):
        """GET a Project."""
        resp, body = self.get("projects/%s" % project_id)
        body = json.loads(body)
        return resp, body['project']

    def delete_project(self, project_id):
        """Delete a project."""
        resp, body = self.delete('projects/%s' % str(project_id))
        return resp, body

    def create_role(self, name):
        """Create a Role."""
        post_body = {
            'name': name
        }
        post_body = json.dumps({'role': post_body})
        resp, body = self.post('roles', post_body)
        body = json.loads(body)
        return resp, body['role']

    def get_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id))
        body = json.loads(body)
        return resp, body['role']

    def update_role(self, name, role_id):
        """Create a Role."""
        post_body = {
            'name': name
        }
        post_body = json.dumps({'role': post_body})
        resp, body = self.patch('roles/%s' % str(role_id), post_body)
        body = json.loads(body)
        return resp, body['role']

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id))
        return resp, body

    def assign_user_role(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None)
        return resp, body

    def create_domain(self, name, **kwargs):
        """Creates a domain."""
        description = kwargs.get('description', None)
        en = kwargs.get('enabled', True)
        post_body = {
            'description': description,
            'enabled': en,
            'name': name
        }
        post_body = json.dumps({'domain': post_body})
        resp, body = self.post('domains', post_body)
        body = json.loads(body)
        return resp, body['domain']

    def delete_domain(self, domain_id):
        """Delete a domain."""
        resp, body = self.delete('domains/%s' % str(domain_id))
        return resp, body

    def list_domains(self):
        """List Domains."""
        resp, body = self.get('domains')
        body = json.loads(body)
        return resp, body['domains']

    def update_domain(self, domain_id, **kwargs):
        """Updates a domain."""
        resp, body = self.get_domain(domain_id)
        description = kwargs.get('description', body['description'])
        en = kwargs.get('enabled', body['enabled'])
        name = kwargs.get('name', body['name'])
        post_body = {
            'description': description,
            'enabled': en,
            'name': name
        }
        post_body = json.dumps({'domain': post_body})
        resp, body = self.patch('domains/%s' % domain_id, post_body)
        body = json.loads(body)
        return resp, body['domain']

    def get_domain(self, domain_id):
        """Get Domain details."""
        resp, body = self.get('domains/%s' % domain_id)
        body = json.loads(body)
        return resp, body['domain']

    def get_token(self, resp_token):
        """Get token details."""
        headers = {'X-Subject-Token': resp_token}
        resp, body = self.get("auth/tokens", headers=headers)
        body = json.loads(body)
        return resp, body['token']

    def delete_token(self, resp_token):
        """Deletes token."""
        headers = {'X-Subject-Token': resp_token}
        resp, body = self.delete("auth/tokens", headers=headers)
        return resp, body

    def create_group(self, name, **kwargs):
        """Creates a group."""
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
        project_id = kwargs.get('project_id', None)
        post_body = {
            'description': description,
            'domain_id': domain_id,
            'project_id': project_id,
            'name': name
        }
        post_body = json.dumps({'group': post_body})
        resp, body = self.post('groups', post_body)
        body = json.loads(body)
        return resp, body['group']

    def get_group(self, group_id):
        """Get group details."""
        resp, body = self.get('groups/%s' % group_id)
        body = json.loads(body)
        return resp, body['group']

    def update_group(self, group_id, **kwargs):
        """Updates a group."""
        resp, body = self.get_group(group_id)
        name = kwargs.get('name', body['name'])
        description = kwargs.get('description', body['description'])
        post_body = {
            'name': name,
            'description': description
        }
        post_body = json.dumps({'group': post_body})
        resp, body = self.patch('groups/%s' % group_id, post_body)
        body = json.loads(body)
        return resp, body['group']

    def delete_group(self, group_id):
        """Delete a group."""
        resp, body = self.delete('groups/%s' % str(group_id))
        return resp, body

    def add_group_user(self, group_id, user_id):
        """Add user into group."""
        resp, body = self.put('groups/%s/users/%s' % (group_id, user_id),
                              None)
        return resp, body

    def list_group_users(self, group_id):
        """List users in group."""
        resp, body = self.get('groups/%s/users' % group_id)
        body = json.loads(body)
        return resp, body['users']

    def list_user_groups(self, user_id):
        """Lists groups which a user belongs to."""
        resp, body = self.get('users/%s/groups' % user_id)
        body = json.loads(body)
        return resp, body['groups']

    def delete_group_user(self, group_id, user_id):
        """Delete user in group."""
        resp, body = self.delete('groups/%s/users/%s' % (group_id, user_id))
        return resp, body

    def assign_user_role_on_project(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None)
        return resp, body

    def assign_user_role_on_domain(self, domain_id, user_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/users/%s/roles/%s' %
                              (domain_id, user_id, role_id), None)
        return resp, body

    def list_user_roles_on_project(self, project_id, user_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/users/%s/roles' %
                              (project_id, user_id))
        body = json.loads(body)
        return resp, body['roles']

    def list_user_roles_on_domain(self, domain_id, user_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/users/%s/roles' %
                              (domain_id, user_id))
        body = json.loads(body)
        return resp, body['roles']

    def revoke_role_from_user_on_project(self, project_id, user_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/users/%s/roles/%s' %
                                 (project_id, user_id, role_id))
        return resp, body

    def revoke_role_from_user_on_domain(self, domain_id, user_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/users/%s/roles/%s' %
                                 (domain_id, user_id, role_id))
        return resp, body

    def assign_group_role_on_project(self, project_id, group_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/groups/%s/roles/%s' %
                              (project_id, group_id, role_id), None)
        return resp, body

    def assign_group_role_on_domain(self, domain_id, group_id, role_id):
        """Add roles to a user on a domain."""
        resp, body = self.put('domains/%s/groups/%s/roles/%s' %
                              (domain_id, group_id, role_id), None)
        return resp, body

    def list_group_roles_on_project(self, project_id, group_id):
        """list roles of a user on a project."""
        resp, body = self.get('projects/%s/groups/%s/roles' %
                              (project_id, group_id))
        body = json.loads(body)
        return resp, body['roles']

    def list_group_roles_on_domain(self, domain_id, group_id):
        """list roles of a user on a domain."""
        resp, body = self.get('domains/%s/groups/%s/roles' %
                              (domain_id, group_id))
        body = json.loads(body)
        return resp, body['roles']

    def revoke_role_from_group_on_project(self, project_id, group_id, role_id):
        """Delete role of a user on a project."""
        resp, body = self.delete('projects/%s/groups/%s/roles/%s' %
                                 (project_id, group_id, role_id))
        return resp, body

    def revoke_role_from_group_on_domain(self, domain_id, group_id, role_id):
        """Delete role of a user on a domain."""
        resp, body = self.delete('domains/%s/groups/%s/roles/%s' %
                                 (domain_id, group_id, role_id))
        return resp, body

    def create_trust(self, trustor_user_id, trustee_user_id, project_id,
                     role_names, impersonation, expires_at):
        """Creates a trust."""
        roles = [{'name': n} for n in role_names]
        post_body = {
            'trustor_user_id': trustor_user_id,
            'trustee_user_id': trustee_user_id,
            'project_id': project_id,
            'impersonation': impersonation,
            'roles': roles,
            'expires_at': expires_at
        }
        post_body = json.dumps({'trust': post_body})
        resp, body = self.post('OS-TRUST/trusts', post_body)
        body = json.loads(body)
        return resp, body['trust']

    def delete_trust(self, trust_id):
        """Deletes a trust."""
        resp, body = self.delete("OS-TRUST/trusts/%s" % trust_id)
        return resp, body

    def get_trusts(self, trustor_user_id=None, trustee_user_id=None):
        """GET trusts."""
        if trustor_user_id:
            resp, body = self.get("OS-TRUST/trusts?trustor_user_id=%s"
                                  % trustor_user_id)
        elif trustee_user_id:
            resp, body = self.get("OS-TRUST/trusts?trustee_user_id=%s"
                                  % trustee_user_id)
        else:
            resp, body = self.get("OS-TRUST/trusts")
        body = json.loads(body)
        return resp, body['trusts']

    def get_trust(self, trust_id):
        """GET trust."""
        resp, body = self.get("OS-TRUST/trusts/%s" % trust_id)
        body = json.loads(body)
        return resp, body['trust']

    def get_trust_roles(self, trust_id):
        """GET roles delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles" % trust_id)
        body = json.loads(body)
        return resp, body['roles']

    def get_trust_role(self, trust_id, role_id):
        """GET role delegated by a trust."""
        resp, body = self.get("OS-TRUST/trusts/%s/roles/%s"
                              % (trust_id, role_id))
        body = json.loads(body)
        return resp, body['role']

    def check_trust_role(self, trust_id, role_id):
        """HEAD Check if role is delegated by a trust."""
        resp, body = self.head("OS-TRUST/trusts/%s/roles/%s"
                               % (trust_id, role_id))
        return resp, body


class V3TokenClientJSON(rest_client.RestClient):

    def __init__(self):
        super(V3TokenClientJSON, self).__init__(None)
        auth_url = CONF.identity.uri_v3
        if not auth_url and CONF.identity_feature_enabled.api_v3:
            raise exceptions.InvalidConfiguration('you must specify a v3 uri '
                                                  'if using the v3 identity '
                                                  'api')
        if 'auth/tokens' not in auth_url:
            auth_url = auth_url.rstrip('/') + '/auth/tokens'

        self.auth_url = auth_url

    def auth(self, user=None, password=None, tenant=None, user_type='id',
             domain=None, token=None):
        """
        :param user: user id or name, as specified in user_type
        :param domain: the user and tenant domain
        :param token: a token to re-scope.

        Accepts different combinations of credentials. Restrictions:
        - tenant and domain are only name (no id)
        - user domain and tenant domain are assumed identical
        - domain scope is not supported here
        Sample sample valid combinations:
        - token
        - token, tenant, domain
        - user_id, password
        - username, password, domain
        - username, password, tenant, domain
        Validation is left to the server side.
        """
        creds = {
            'auth': {
                'identity': {
                    'methods': [],
                }
            }
        }
        id_obj = creds['auth']['identity']
        if token:
            id_obj['methods'].append('token')
            id_obj['token'] = {
                'id': token
            }
        if user and password:
            id_obj['methods'].append('password')
            id_obj['password'] = {
                'user': {
                    'password': password,
                }
            }
            if user_type == 'id':
                id_obj['password']['user']['id'] = user
            else:
                id_obj['password']['user']['name'] = user
            if domain is not None:
                _domain = dict(name=domain)
                id_obj['password']['user']['domain'] = _domain
        if tenant is not None:
            _domain = dict(name=domain)
            project = dict(name=tenant, domain=_domain)
            scope = dict(project=project)
            creds['auth']['scope'] = scope

        body = json.dumps(creds)
        resp, body = self.post(self.auth_url, body=body)
        return resp, body

    def request(self, method, url, extra_headers=False, headers=None,
                body=None):
        """A simple HTTP request interface."""
        if headers is None:
            # Always accept 'json', for xml token client too.
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
        elif resp.status not in [200, 201, 204]:
            raise exceptions.IdentityError(
                'Unexpected status code {0}'.format(resp.status))

        return resp, json.loads(resp_body)

    def get_token(self, user, password, tenant, domain='Default',
                  auth_data=False):
        """
        :param user: username
        Returns (token id, token data) for supplied credentials
        """
        resp, body = self.auth(user, password, tenant, user_type='name',
                               domain=domain)

        token = resp.get('x-subject-token')
        if auth_data:
            return token, body['token']
        else:
            return token
