# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from urlparse import urlparse

from tempest.common.rest_client import RestClient


class IdentityV3ClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(IdentityV3ClientJSON, self).__init__(config, username, password,
                                                   auth_url, tenant_name)
        self.service = self.config.identity.catalog_type
        self.endpoint_url = 'adminURL'

    def request(self, method, url, headers=None, body=None, wait=None):
        """Overriding the existing HTTP request in super class rest_client."""
        self._set_auth()
        self.base_url = self.base_url.replace(urlparse(self.base_url).path,
                                              "/v3")
        return super(IdentityV3ClientJSON, self).request(method, url,
                                                         headers=headers,
                                                         body=body)

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
        resp, body = self.post('users', post_body,
                               self.headers)
        body = json.loads(body)
        return resp, body['user']

    def update_user(self, user_id, name, **kwargs):
        """Updates a user."""
        email = kwargs.get('email', None)
        en = kwargs.get('enabled', True)
        project_id = kwargs.get('project_id', None)
        description = kwargs.get('description', None)
        domain_id = kwargs.get('domain_id', 'default')
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
        resp, body = self.patch('users/%s' % user_id, post_body,
                                self.headers)
        body = json.loads(body)
        return resp, body['user']

    def list_user_projects(self, user_id):
        """Lists the projects on which a user has roles assigned."""
        resp, body = self.get('users/%s/projects' % user_id, self.headers)
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
        resp, body = self.post('projects', post_body, self.headers)
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
        resp, body = self.post('roles', post_body, self.headers)
        body = json.loads(body)
        return resp, body['role']

    def get_role(self, role_id):
        """GET a Role."""
        resp, body = self.get('roles/%s' % str(role_id))
        body = json.loads(body)
        return resp, body['role']

    def delete_role(self, role_id):
        """Delete a role."""
        resp, body = self.delete('roles/%s' % str(role_id))
        return resp, body

    def assign_user_role(self, project_id, user_id, role_id):
        """Add roles to a user on a project."""
        resp, body = self.put('projects/%s/users/%s/roles/%s' %
                              (project_id, user_id, role_id), None,
                              self.headers)
        return resp, body
