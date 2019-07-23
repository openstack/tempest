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

from tempest.lib.api_schema.response.compute.v2_1 import \
    security_groups as schema
from tempest.lib.common import rest_client
from tempest.lib.services.compute import base_compute_client


class SecurityGroupRulesClient(base_compute_client.BaseComputeClient):

    def create_security_group_rule(self, **kwargs):
        """Create a new security group rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/compute/#create-security-group-rule
        """
        post_body = json.dumps({'security_group_rule': kwargs})
        url = 'os-security-group-rules'
        resp, body = self.post(url, post_body)
        body = json.loads(body)
        self.validate_response(schema.create_security_group_rule, resp, body)
        return rest_client.ResponseBody(resp, body)

    def delete_security_group_rule(self, group_rule_id):
        """Deletes the provided Security Group rule."""
        resp, body = self.delete('os-security-group-rules/%s' %
                                 group_rule_id)
        self.validate_response(schema.delete_security_group_rule, resp, body)
        return rest_client.ResponseBody(resp, body)
