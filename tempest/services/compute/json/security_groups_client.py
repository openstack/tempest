# Copyright 2012 OpenStack Foundation
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
from six.moves.urllib import parse as urllib
from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import security_groups as schema
from tempest.common import service_client


class SecurityGroupsClient(service_client.ServiceClient):

    def list_security_groups(self, **params):
        """List all security groups for a user."""

        url = 'os-security-groups'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_security_groups, resp, body)
        return service_client.ResponseBody(resp, body)

    def show_security_group(self, security_group_id):
        """Get the details of a Security Group."""
        url = "os-security-groups/%s" % security_group_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_security_group(self, **kwargs):
        """Creates a new security group.

        name (Required): Name of security group.
        description (Required): Description of security group.
        """
        post_body = json.dumps({'security_group': kwargs})
        resp, body = self.post('os-security-groups', post_body)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return service_client.ResponseBody(resp, body)

    def update_security_group(self, security_group_id, **kwargs):
        """Update a security group.

        security_group_id: a security_group to update
        name: new name of security group
        description: new description of security group
        """
        post_body = json.dumps({'security_group': kwargs})
        resp, body = self.put('os-security-groups/%s' % security_group_id,
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.update_security_group, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_security_group(self, security_group_id):
        """Deletes the provided Security Group."""
        resp, body = self.delete(
            'os-security-groups/%s' % security_group_id)
        self.validate_response(schema.delete_security_group, resp, body)
        return service_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_security_group(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'security_group'
