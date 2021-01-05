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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class UsersClient(rest_client.RestClient):
    api_version = "v3"

    def create_user(self, **kwargs):
        """Creates a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#create-user
        """
        post_body = json.dumps({'user': kwargs})
        resp, body = self.post('users', post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user(self, user_id, **kwargs):
        """Updates a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#update-user
        """
        if 'id' not in kwargs:
            kwargs['id'] = user_id
        post_body = json.dumps({'user': kwargs})
        resp, body = self.patch('users/%s' % user_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user_password(self, user_id, **kwargs):
        """Update a user password

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/index.html#change-password-for-user
        """
        update_user = json.dumps({'user': kwargs})
        resp, _ = self.post('users/%s/password' % user_id, update_user)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_user_projects(self, user_id, **params):
        """Lists the projects on which a user has roles assigned.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-projects-for-user
        """
        url = 'users/%s/projects' % user_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def list_users(self, **params):
        """Get the list of users.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-users
        """
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

    def list_user_groups(self, user_id, **params):
        """Lists groups which a user belongs to.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v3/#list-groups-to-which-a-user-belongs
        """
        url = 'users/%s/groups' % user_id
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_user_ec2_credential(self, user_id, **kwargs):
        post_body = json.dumps(kwargs)
        resp, body = self.post('/users/%s/credentials/OS-EC2' % user_id,
                               post_body)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_user_ec2_credential(self, user_id, access):
        resp, body = self.delete('/users/%s/credentials/OS-EC2/%s' %
                                 (user_id, access))
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_user_ec2_credentials(self, user_id):
        resp, body = self.get('/users/%s/credentials/OS-EC2' % user_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_user_ec2_credential(self, user_id, access):
        resp, body = self.get('/users/%s/credentials/OS-EC2/%s' %
                              (user_id, access))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
