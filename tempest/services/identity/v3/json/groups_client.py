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

from oslo_serialization import jsonutils as json

from tempest.common import service_client


class GroupsClient(service_client.ServiceClient):
    api_version = "v3"

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
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def get_group(self, group_id):
        """Get group details."""
        resp, body = self.get('groups/%s' % group_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def list_groups(self):
        """Lists the groups."""
        resp, body = self.get('groups')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def update_group(self, group_id, **kwargs):
        """Updates a group."""
        body = self.get_group(group_id)['group']
        name = kwargs.get('name', body['name'])
        description = kwargs.get('description', body['description'])
        post_body = {
            'name': name,
            'description': description
        }
        post_body = json.dumps({'group': post_body})
        resp, body = self.patch('groups/%s' % group_id, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_group(self, group_id):
        """Delete a group."""
        resp, body = self.delete('groups/%s' % str(group_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def add_group_user(self, group_id, user_id):
        """Add user into group."""
        resp, body = self.put('groups/%s/users/%s' % (group_id, user_id),
                              None)
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)

    def list_group_users(self, group_id):
        """List users in group."""
        resp, body = self.get('groups/%s/users' % group_id)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def delete_group_user(self, group_id, user_id):
        """Delete user in group."""
        resp, body = self.delete('groups/%s/users/%s' % (group_id, user_id))
        self.expected_success(204, resp.status)
        return service_client.ResponseBody(resp, body)
