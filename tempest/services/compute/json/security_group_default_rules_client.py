# Copyright 2014 NEC Corporation.
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

CONF = config.CONF


class SecurityGroupDefaultRulesClientJSON(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(SecurityGroupDefaultRulesClientJSON,
              self).__init__(auth_provider)
        self.service = CONF.compute.catalog_type

    def create_security_default_group_rule(self, ip_protocol, from_port,
                                           to_port, **kwargs):
        """
        Creating security group default rules.
        ip_protocol : ip_protocol (icmp, tcp, udp).
        from_port: Port at start of range.
        to_port  : Port at end of range.
        cidr     : CIDR for address range.
        """
        post_body = {
            'ip_protocol': ip_protocol,
            'from_port': from_port,
            'to_port': to_port,
            'cidr': kwargs.get('cidr'),
        }
        post_body = json.dumps({'security_group_default_rule': post_body})
        url = 'os-security-group-default-rules'
        resp, body = self.post(url, post_body)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['security_group_default_rule']

    def delete_security_group_default_rule(self,
                                           security_group_default_rule_id):
        """Deletes the provided Security Group default rule."""
        resp, body = self.delete('os-security-group-default-rules/%s' % str(
            security_group_default_rule_id))
        self.expected_success(204, resp.status)
        return resp, body

    def list_security_group_default_rules(self):
        """List all Security Group default rules."""
        resp, body = self.get('os-security-group-default-rules')
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['security_group_default_rules']

    def get_security_group_default_rule(self, security_group_default_rule_id):
        """Return the details of provided Security Group default rule."""
        resp, body = self.get('os-security-group-default-rules/%s' % str(
            security_group_default_rule_id))
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return resp, body['security_group_default_rule']
