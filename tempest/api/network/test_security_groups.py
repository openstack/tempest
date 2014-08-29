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

import six

from tempest.api.network import base_security_groups as base
from tempest.common.utils import data_utils
from tempest import test


class SecGroupTest(base.BaseSecGroupTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecGroupTest, cls).setUpClass()
        if not test.is_extension_enabled('security-group', 'network'):
            msg = "security-group extension not enabled."
            raise cls.skipException(msg)

    @test.attr(type='smoke')
    def test_list_security_groups(self):
        # Verify the that security group belonging to tenant exist in list
        _, body = self.client.list_security_groups()
        security_groups = body['security_groups']
        found = None
        for n in security_groups:
            if (n['name'] == 'default'):
                found = n['id']
        msg = "Security-group list doesn't contain default security-group"
        self.assertIsNotNone(found, msg)

    @test.attr(type='smoke')
    def test_create_list_update_show_delete_security_group(self):
        group_create_body, name = self._create_security_group()

        # List security groups and verify if created group is there in response
        _, list_body = self.client.list_security_groups()
        secgroup_list = list()
        for secgroup in list_body['security_groups']:
            secgroup_list.append(secgroup['id'])
        self.assertIn(group_create_body['security_group']['id'], secgroup_list)
        # Update the security group
        new_name = data_utils.rand_name('security-')
        new_description = data_utils.rand_name('security-description')
        _, update_body = self.client.update_security_group(
            group_create_body['security_group']['id'],
            name=new_name,
            description=new_description)
        # Verify if security group is updated
        self.assertEqual(update_body['security_group']['name'], new_name)
        self.assertEqual(update_body['security_group']['description'],
                         new_description)
        # Show details of the updated security group
        resp, show_body = self.client.show_security_group(
            group_create_body['security_group']['id'])
        self.assertEqual(show_body['security_group']['name'], new_name)
        self.assertEqual(show_body['security_group']['description'],
                         new_description)

    @test.attr(type='smoke')
    def test_create_show_delete_security_group_rule(self):
        group_create_body, _ = self._create_security_group()

        # Create rules for each protocol
        protocols = ['tcp', 'udp', 'icmp']
        for protocol in protocols:
            _, rule_create_body = self.client.create_security_group_rule(
                security_group_id=group_create_body['security_group']['id'],
                protocol=protocol,
                direction='ingress'
            )

            # Show details of the created security rule
            _, show_rule_body = self.client.show_security_group_rule(
                rule_create_body['security_group_rule']['id']
            )
            create_dict = rule_create_body['security_group_rule']
            for key, value in six.iteritems(create_dict):
                self.assertEqual(value,
                                 show_rule_body['security_group_rule'][key],
                                 "%s does not match." % key)

            # List rules and verify created rule is in response
            _, rule_list_body = self.client.list_security_group_rules()
            rule_list = [rule['id']
                         for rule in rule_list_body['security_group_rules']]
            self.assertIn(rule_create_body['security_group_rule']['id'],
                          rule_list)

    @test.attr(type='smoke')
    def test_create_security_group_rule_with_additional_args(self):
        # Verify creating security group rule with the following
        # arguments works: "protocol": "tcp", "port_range_max": 77,
        # "port_range_min": 77, "direction":"ingress".
        group_create_body, _ = self._create_security_group()

        direction = 'ingress'
        protocol = 'tcp'
        port_range_min = 77
        port_range_max = 77
        _, rule_create_body = self.client.create_security_group_rule(
            security_group_id=group_create_body['security_group']['id'],
            direction=direction,
            protocol=protocol,
            port_range_min=port_range_min,
            port_range_max=port_range_max
        )

        sec_group_rule = rule_create_body['security_group_rule']

        self.assertEqual(sec_group_rule['direction'], direction)
        self.assertEqual(sec_group_rule['protocol'], protocol)
        self.assertEqual(int(sec_group_rule['port_range_min']), port_range_min)
        self.assertEqual(int(sec_group_rule['port_range_max']), port_range_max)


class SecGroupTestXML(SecGroupTest):
    _interface = 'xml'
