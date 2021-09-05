# Copyright (c) 2019 Ericsson
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

from tempest.lib.services.network import base


class QosMinimumBandwidthRulesClient(base.BaseNetworkClient):

    def create_minimum_bandwidth_rule(self, qos_policy_id, **kwargs):
        """Creates a minimum bandwidth rule for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-minimum-bandwidth-rule
        """
        uri = '/qos/policies/%s/minimum_bandwidth_rules' % qos_policy_id
        post_data = {'minimum_bandwidth_rule': kwargs}
        return self.create_resource(uri, post_data)

    def update_minimum_bandwidth_rule(self, qos_policy_id, rule_id, **kwargs):
        """Updates a minimum bandwidth rule.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-minimum-bandwidth-rule
        """
        uri = '/qos/policies/%s/minimum_bandwidth_rules/%s' % (
            qos_policy_id, rule_id)
        post_data = {'minimum_bandwidth_rule': kwargs}
        return self.update_resource(uri, post_data)

    def show_minimum_bandwidth_rule(self, qos_policy_id, rule_id, **fields):
        """Show details of a minimum bandwidth rule.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-minimum-bandwidth-rule-details
        """
        uri = '/qos/policies/%s/minimum_bandwidth_rules/%s' % (
            qos_policy_id, rule_id)
        return self.show_resource(uri, **fields)

    def delete_minimum_bandwidth_rule(self, qos_policy_id, rule_id):
        """Deletes a minimum bandwidth rule for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-minimum-bandwidth-rule
        """
        uri = '/qos/policies/%s/minimum_bandwidth_rules/%s' % (
            qos_policy_id, rule_id)
        return self.delete_resource(uri)

    def list_minimum_bandwidth_rules(self, qos_policy_id, **filters):
        """Lists all minimum bandwidth rules for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-minimum-bandwidth-rules-for-qos-policy
        """
        uri = '/qos/policies/%s/minimum_bandwidth_rules' % qos_policy_id
        return self.list_resources(uri, **filters)
