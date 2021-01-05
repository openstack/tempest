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

from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.api_schema.response.compute.v2_1 import \
    security_groups as schema
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest.lib.services.compute import base_compute_client


class SecurityGroupsClient(base_compute_client.BaseComputeClient):

    def list_security_groups(self, **params):
        """List all security groups for a user.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#list-security-groups
        """

        url = 'os-security-groups'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_security_groups, resp, body)
        return rest_client.ResponseBody(resp, body)

    def show_security_group(self, security_group_id):
        """Get the details of a Security Group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#show-security-group-details
        """
        url = "os-security-groups/%s" % security_group_id
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def create_security_group(self, **kwargs):
        """Create a new security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-security-group
        """
        post_body = json.dumps({'security_group': kwargs})
        resp, body = self.post('os-security-groups', post_body)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def update_security_group(self, security_group_id, **kwargs):
        """Update a security group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#update-security-group
        """
        post_body = json.dumps({'security_group': kwargs})
        resp, body = self.put('os-security-groups/%s' % security_group_id,
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.update_security_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_security_group(self, security_group_id):
        """Delete the provided Security Group.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#delete-security-group
        """
        resp, body = self.delete(
            'os-security-groups/%s' % security_group_id)
        self.validate_response(schema.delete_security_group, resp, body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_security_group(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Return the primary type of resource this client works with."""
        return 'security_group'
