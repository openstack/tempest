# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation
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

from tempest.api.network import base
from tempest.common.utils import data_utils


class BaseSecGroupTest(base.BaseNetworkTest):

    @classmethod
    def setUpClass(cls):
        super(BaseSecGroupTest, cls).setUpClass()

    def _create_security_group(self):
        # Create a security group
        name = data_utils.rand_name('secgroup-')
        resp, group_create_body = self.client.create_security_group(name)
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_security_group,
                        group_create_body['security_group']['id'])
        self.assertEqual(group_create_body['security_group']['name'], name)
        return group_create_body, name

    def _delete_security_group(self, secgroup_id):
        resp, _ = self.client.delete_security_group(secgroup_id)
        self.assertEqual(204, resp.status)
        # Asserting that the security group is not found in the list
        # after deletion
        resp, list_body = self.client.list_security_groups()
        self.assertEqual('200', resp['status'])
        secgroup_list = list()
        for secgroup in list_body['security_groups']:
            secgroup_list.append(secgroup['id'])
        self.assertNotIn(secgroup_id, secgroup_list)

    def _delete_security_group_rule(self, rule_id):
        resp, _ = self.client.delete_security_group_rule(rule_id)
        self.assertEqual(204, resp.status)
        # Asserting that the security group is not found in the list
        # after deletion
        resp, list_body = self.client.list_security_group_rules()
        self.assertEqual('200', resp['status'])
        rules_list = list()
        for rule in list_body['security_group_rules']:
            rules_list.append(rule['id'])
        self.assertNotIn(rule_id, rules_list)
