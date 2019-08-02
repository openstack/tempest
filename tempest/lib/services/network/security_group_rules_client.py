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

from tempest.lib.services.network import base


class SecurityGroupRulesClient(base.BaseNetworkClient):

    def create_security_group_rule(self, **kwargs):
        """Creates an OpenStack Networking security group rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-security-group-rule
        """
        uri = '/security-group-rules'
        post_data = {'security_group_rule': kwargs}
        return self.create_resource(uri, post_data)

    def show_security_group_rule(self, security_group_rule_id, **fields):
        """Shows detailed information for a security group rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-security-group-rule
        """
        uri = '/security-group-rules/%s' % security_group_rule_id
        return self.show_resource(uri, **fields)

    def delete_security_group_rule(self, security_group_rule_id):
        uri = '/security-group-rules/%s' % security_group_rule_id
        return self.delete_resource(uri)

    def list_security_group_rules(self, **filters):
        """Lists a summary of all OpenStack Networking security group rules.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-security-group-rules
        """
        uri = '/security-group-rules'
        return self.list_resources(uri, **filters)
