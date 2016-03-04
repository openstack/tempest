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


class UsersClient(rest_client.RestClient):
    api_version = "v3"

    def create_user(self, user_name, password=None, project_id=None,
                    email=None, domain_id='default', **kwargs):
        """Creates a user."""
        en = kwargs.get('enabled', True)
        description = kwargs.get('description', None)
        default_project_id = kwargs.get('default_project_id')
        post_body = {
            'project_id': project_id,
            'default_project_id': default_project_id,
            'description': description,
            'domain_id': domain_id,
            'email': email,
            'enabled': en,
            'name': user_name,
            'password': password
        }
        post_body = json.dumps({'user': post_body})
        resp, body = self.post('users', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user(self, user_id, name, **kwargs):
        """Updates a user."""
        body = self.show_user(user_id)['user']
        email = kwargs.get('email', body['email'])
        en = kwargs.get('enabled', body['enabled'])
        project_id = kwargs.get('project_id', body['project_id'])
        if 'default_project_id' in body.keys():
            default_project_id = kwargs.get('default_project_id',
                                            body['default_project_id'])
        else:
            default_project_id = kwargs.get('default_project_id')
        description = kwargs.get('description', body['description'])
        domain_id = kwargs.get('domain_id', body['domain_id'])
        post_body = {
            'name': name,
            'email': email,
            'enabled': en,
            'project_id': project_id,
            'default_project_id': default_project_id,
            'id': user_id,
            'domain_id': domain_id,
            'description': description
        }
        post_body = json.dumps({'user': post_body})
        resp, body = self.patch('users/%s' % user_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user_password(self, user_id, **kwargs):
        """Update a user password

        Available params: see http://developer.openstack.org/
                              api-ref-identity-v3.html#changeUserPassword
        """
        update_user = json.dumps({'user': kwargs})
        resp, _ = self.post('users/%s/password' % user_id, update_user)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_user_projects(self, user_id):
        """Lists the projects on which a user has roles assigned."""
        resp, body = self.get('users/%s/projects' % user_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_users(self, params=None):
        """Get the list of users."""
        url = 'users'
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_user(self, user_id):
        """GET a user."""
        resp, body = self.get("users/%s" % user_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_user(self, user_id):
        """Deletes a User."""
        resp, body = self.delete("users/%s" % user_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_user_groups(self, user_id):
        """Lists groups which a user belongs to."""
        resp, body = self.get('users/%s/groups' % user_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
