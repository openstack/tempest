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


class MeteringLabelRulesClient(base.BaseNetworkClient):

    def create_metering_label_rule(self, **kwargs):
        """Create metering label rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#create-metering-label-rule
        """
        uri = '/metering/metering-label-rules'
        post_data = {'metering_label_rule': kwargs}
        return self.create_resource(uri, post_data)

    def show_metering_label_rule(self, metering_label_rule_id, **fields):
        uri = '/metering/metering-label-rules/%s' % metering_label_rule_id
        return self.show_resource(uri, **fields)

    def delete_metering_label_rule(self, metering_label_rule_id):
        uri = '/metering/metering-label-rules/%s' % metering_label_rule_id
        return self.delete_resource(uri)

    def list_metering_label_rules(self, **filters):
        """List metering label rules.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#list-metering-label-rules
        """
        uri = '/metering/metering-label-rules'
        return self.list_resources(uri, **filters)
