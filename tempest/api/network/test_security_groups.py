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
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class SecGroupTest(base.BaseNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecGroupTest, cls).setUpClass()

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

    @attr(type='smoke')
    def test_list_security_groups(self):
        # Verify the that security group belonging to tenant exist in list
        resp, body = self.client.list_security_groups()
        self.assertEqual('200', resp['status'])
        security_groups = body['security_groups']
        found = None
        for n in security_groups:
            if (n['name'] == 'default'):
                found = n['id']
        msg = "Security-group list doesn't contain default security-group"
        self.assertIsNotNone(found, msg)

    @attr(type='smoke')
    def test_create_show_delete_security_group_and_rule(self):
        # Create a security group
        name = rand_name('secgroup-')
        resp, group_create_body = self.client.create_security_group(name)
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_security_group,
                        group_create_body['security_group']['id'])
        self.assertEqual(group_create_body['security_group']['name'], name)

        # Show details of the created security group
        resp, show_body = self.client.show_security_group(
            group_create_body['security_group']['id'])
        self.assertEqual('200', resp['status'])
        self.assertEqual(show_body['security_group']['name'], name)

        # List security groups and verify if created group is there in response
        resp, list_body = self.client.list_security_groups()
        self.assertEqual('200', resp['status'])
        secgroup_list = list()
        for secgroup in list_body['security_groups']:
            secgroup_list.append(secgroup['id'])
        self.assertIn(group_create_body['security_group']['id'], secgroup_list)
        # No Update in security group
        # Create rule
        resp, rule_create_body = self.client.create_security_group_rule(
            group_create_body['security_group']['id']
        )
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_security_group_rule,
                        rule_create_body['security_group_rule']['id'])
        # Show details of the created security rule
        resp, show_rule_body = self.client.show_security_group_rule(
            rule_create_body['security_group_rule']['id']
        )
        self.assertEqual('200', resp['status'])

        # List rules and verify created rule is in response
        resp, rule_list_body = self.client.list_security_group_rules()
        self.assertEqual('200', resp['status'])
        rule_list = [rule['id']
                     for rule in rule_list_body['security_group_rules']]
        self.assertIn(rule_create_body['security_group_rule']['id'], rule_list)

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_security_group(self):
        non_exist_id = rand_name('secgroup-')
        self.assertRaises(exceptions.NotFound, self.client.show_security_group,
                          non_exist_id)

    @attr(type=['negative', 'smoke'])
    def test_show_non_existent_security_group_rule(self):
        non_exist_id = rand_name('rule-')
        self.assertRaises(exceptions.NotFound,
                          self.client.show_security_group_rule,
                          non_exist_id)


class SecGroupTestXML(SecGroupTest):
    _interface = 'xml'
