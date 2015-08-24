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

from tempest_lib import exceptions as lib_exc

from tempest.api_schema.response.compute.v2_1 import security_groups as schema
from tempest.common import service_client


class SecurityGroupRulesClient(service_client.ServiceClient):

    def create_security_group_rule(self, **kwargs):
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
        post_body = json.dumps({'security_group_rule': kwargs})
        url = 'os-security-group-rules'
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_security_group_rule, resp, body)
        return service_client.ResponseBody(resp, body)

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule."""
        resp, body = self.delete('os-security-group-rules/%s' %
                                 group_rule_id)
        self.validate_response(schema.delete_security_group_rule, resp, body)
        return service_client.ResponseBody(resp, body)

    def list_security_group_rules(self, security_group_id):
        """List all rules for a security group."""
        resp, body = self.get('os-security-groups')
        body = json.loads(body)
        self.validate_response(schema.list_security_groups, resp, body)
        for sg in body['security_groups']:
            if sg['id'] == security_group_id:
                return service_client.ResponseBody(resp, sg)
        raise lib_exc.NotFound('No such Security Group')
