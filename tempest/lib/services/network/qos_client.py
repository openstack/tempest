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


class QosClient(base.BaseNetworkClient):

    def create_qos_policy(self, **kwargs):
        """Creates a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-qos-policy
        """
        uri = '/qos/policies'
        post_data = {'policy': kwargs}
        return self.create_resource(uri, post_data)

    def update_qos_policy(self, qos_policy_id, **kwargs):
        """Updates a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-qos-policy
        """
        uri = '/qos/policies/%s' % qos_policy_id
        post_data = {'policy': kwargs}
        return self.update_resource(uri, post_data)

    def show_qos_policy(self, qos_policy_id, **fields):
        """Show details of a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-qos-policy-details
        """
        uri = '/qos/policies/%s' % qos_policy_id
        return self.show_resource(uri, **fields)

    def delete_qos_policy(self, qos_policy_id):
        """Deletes a QoS policy.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-qos-policy
        """
        uri = '/qos/policies/%s' % qos_policy_id
        return self.delete_resource(uri)

    def list_qos_policies(self, **filters):
        """Lists QoS policies.

        For full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-qos-policies
        """
        uri = '/qos/policies'
        return self.list_resources(uri, **filters)
