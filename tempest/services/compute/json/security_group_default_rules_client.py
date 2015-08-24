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

from oslo_serialization import jsonutils as json

from tempest.api_schema.response.compute.v2_1 import \
    security_group_default_rule as schema
from tempest.common import service_client


class SecurityGroupDefaultRulesClient(service_client.ServiceClient):

    def create_security_default_group_rule(self, **kwargs):
        """
        Creating security group default rules.
        ip_protocol : ip_protocol (icmp, tcp, udp).
        from_port: Port at start of range.
        to_port  : Port at end of range.
        cidr     : CIDR for address range.
        """
        post_body = json.dumps({'security_group_default_rule': kwargs})
        url = 'os-security-group-default-rules'
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_get_security_group_default_rule,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_security_group_default_rule(self,
                                           security_group_default_rule_id):
        """Deletes the provided Security Group default rule."""
        resp, body = self.delete('os-security-group-default-rules/%s' % (
            security_group_default_rule_id))
        self.validate_response(schema.delete_security_group_default_rule,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def list_security_group_default_rules(self):
        """List all Security Group default rules."""
        resp, body = self.get('os-security-group-default-rules')
        body = json.loads(body)
        self.validate_response(schema.list_security_group_default_rules,
                               resp, body)
        return service_client.ResponseBody(resp, body)

    def show_security_group_default_rule(self, security_group_default_rule_id):
        """Return the details of provided Security Group default rule."""
        resp, body = self.get('os-security-group-default-rules/%s' %
                              security_group_default_rule_id)
        body = json.loads(body)
        self.validate_response(schema.create_get_security_group_default_rule,
                               resp, body)
        return service_client.ResponseBody(resp, body)
