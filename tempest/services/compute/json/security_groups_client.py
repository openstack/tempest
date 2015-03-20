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

import json
import urllib

from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import security_groups as schema
from tempest.common import service_client


class SecurityGroupsClientJSON(service_client.ServiceClient):

    def list_security_groups(self, params=None):
        """List all security groups for a user."""

        url = 'os-security-groups'
        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.list_security_groups, resp, body)
        return service_client.ResponseBodyList(resp, body['security_groups'])

    def get_security_group(self, security_group_id):
        """Get the details of a Security Group."""
        url = "os-security-groups/%s" % str(security_group_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return service_client.ResponseBody(resp, body['security_group'])

    def create_security_group(self, name, description):
        """
        Creates a new security group.
        name (Required): Name of security group.
        description (Required): Description of security group.
        """
        post_body = {
            'name': name,
            'description': description,
        }
        post_body = json.dumps({'security_group': post_body})
        resp, body = self.post('os-security-groups', post_body)
        body = json.loads(body)
        self.validate_response(schema.get_security_group, resp, body)
        return service_client.ResponseBody(resp, body['security_group'])

    def update_security_group(self, security_group_id, name=None,
                              description=None):
        """
        Update a security group.
        security_group_id: a security_group to update
        name: new name of security group
        description: new description of security group
        """
        post_body = {}
        if name:
            post_body['name'] = name
        if description:
            post_body['description'] = description
        post_body = json.dumps({'security_group': post_body})
        resp, body = self.put('os-security-groups/%s' % str(security_group_id),
                              post_body)
        body = json.loads(body)
        self.validate_response(schema.update_security_group, resp, body)
        return service_client.ResponseBody(resp, body['security_group'])

    def delete_security_group(self, security_group_id):
        """Deletes the provided Security Group."""
        resp, body = self.delete(
            'os-security-groups/%s' % str(security_group_id))
        self.validate_response(schema.delete_security_group, resp, body)
        return service_client.ResponseBody(resp, body)

    def create_security_group_rule(self, parent_group_id, ip_proto, from_port,
                                   to_port, **kwargs):
        """
        Creating a new security group rules.
        parent_group_id :ID of Security group
        ip_protocol : ip_proto (icmp, tcp, udp).
        from_port: Port at start of range.
        to_port  : Port at end of range.
        Following optional keyword arguments are accepted:
        cidr     : CIDR for address range.
        group_id : ID of the Source group
        """
        post_body = {
            'parent_group_id': parent_group_id,
            'ip_protocol': ip_proto,
            'from_port': from_port,
            'to_port': to_port,
            'cidr': kwargs.get('cidr'),
            'group_id': kwargs.get('group_id'),
        }
        post_body = json.dumps({'security_group_rule': post_body})
        url = 'os-security-group-rules'
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_security_group_rule, resp, body)
        return service_client.ResponseBody(resp, body['security_group_rule'])

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule."""
        resp, body = self.delete('os-security-group-rules/%s' %
                                 str(group_rule_id))
        self.validate_response(schema.delete_security_group_rule, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_security_group_rules(self, security_group_id):
        """List all rules for a security group."""
        resp, body = self.get('os-security-groups')
        body = json.loads(body)
        self.validate_response(schema.list_security_groups, resp, body)
        for sg in body['security_groups']:
            if sg['id'] == security_group_id:
                return service_client.ResponseBodyList(resp, sg['rules'])
        raise lib_exc.NotFound('No such Security Group')

    def is_resource_deleted(self, id):
        try:
            self.get_security_group(id)
        except lib_exc.NotFound:
            return True
        return False

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'security_group'
