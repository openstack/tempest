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


class UsersClient(rest_client.RestClient):
    api_version = "v2.0"

    def create_user(self, **kwargs):
        """Create a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#create-user-admin-endpoint
        """
        post_body = json.dumps({'user': kwargs})
        resp, body = self.post('users', post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user(self, user_id, **kwargs):
        """Updates a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#update-user-admin-endpoint
        """
        put_body = json.dumps({'user': kwargs})
        resp, body = self.put('users/%s' % user_id, put_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_user(self, user_id):
        """GET a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#show-user-details-admin-endpoint
        """
        resp, body = self.get("users/%s" % user_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def delete_user(self, user_id):
        """Delete a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#delete-user-admin-endpoint
        """
        resp, body = self.delete("users/%s" % user_id)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_users(self, **params):
        """Get the list of users.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-admin/index.html#list-users-admin-endpoint
        """
        url = "users"
        if params:
            url += '?%s' % urllib.urlencode(params)
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user_enabled(self, user_id, **kwargs):
        """Enables or disables a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/identity/v2-ext/index.html#enable-disable-user
        """
        # NOTE: The URL (users/<id>/enabled) is different from the api-site
        # one (users/<id>/OS-KSADM/enabled) , but they are the same API
        # because of the fact that in keystone/contrib/admin_crud/core.py
        # both api use same action='set_user_enabled'
        put_body = json.dumps({'user': kwargs})
        resp, body = self.put('users/%s/enabled' % user_id, put_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user_password(self, user_id, **kwargs):
        """Update User Password."""
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1524147
        put_body = json.dumps({'user': kwargs})
        resp, body = self.put('users/%s/OS-KSADM/password' % user_id, put_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def update_user_own_password(self, user_id, **kwargs):
        """User updates own password"""
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1524153
        # NOTE: This API is used for updating user password by itself.
        # Ref: http://lists.openstack.org/pipermail/openstack-dev/2015-December
        #      /081803.html
        patch_body = json.dumps({'user': kwargs})
        resp, body = self.patch('OS-KSCRUD/users/%s' % user_id, patch_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_user_ec2_credential(self, user_id, **kwargs):
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        post_body = json.dumps(kwargs)
        resp, body = self.post('/users/%s/credentials/OS-EC2' % user_id,
                               post_body)
        self.expected_success(200, resp.status)
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
