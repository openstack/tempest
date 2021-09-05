# Copyright 2021 Red Hat.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib.services.network import base


class QosLimitBandwidthRulesClient(base.BaseNetworkClient):

    def create_limit_bandwidth_rule(self, qos_policy_id, **kwargs):
        """Creates a limit bandwidth rule for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-bandwidth-limit-rule
        """
        uri = '/qos/policies/{}/bandwidth_limit_rules'.format(
            qos_policy_id)
        post_data = {'bandwidth_limit_rule': kwargs}
        return self.create_resource(uri, post_data)

    def update_limit_bandwidth_rule(self, qos_policy_id, rule_id, **kwargs):
        """Updates a limit bandwidth rule.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-bandwidth-limit-rule
        """
        uri = '/qos/policies/{}/bandwidth_limit_rules/{}'.format(
            qos_policy_id, rule_id)
        post_data = {'bandwidth_limit_rule': kwargs}
        return self.update_resource(uri, post_data)

    def show_limit_bandwidth_rule(self, qos_policy_id, rule_id, **fields):
        """Show details of a limit bandwidth rule.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-bandwidth-limit-rule-details
        """
        uri = '/qos/policies/{}/bandwidth_limit_rules/{}'.format(
            qos_policy_id, rule_id)
        return self.show_resource(uri, **fields)

    def delete_limit_bandwidth_rule(self, qos_policy_id, rule_id):
        """Deletes a limit bandwidth rule for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-bandwidth-limit-rule
        """
        uri = '/qos/policies/{}/bandwidth_limit_rules/{}'.format(
            qos_policy_id, rule_id)
        return self.delete_resource(uri)

    def list_limit_bandwidth_rules(self, qos_policy_id, **filters):
        """Lists all limit bandwidth rules for a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-bandwidth-limit-rules-for-qos-policy
        """
        uri = '/qos/policies/{}/bandwidth_limit_rules'.format(qos_policy_id)
        return self.list_resources(uri, **filters)
