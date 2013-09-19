# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.thirdparty.boto.test import BotoTestCase


class EC2SecurityGroupTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(EC2SecurityGroupTest, cls).setUpClass()
        cls.os = clients.Manager()
        cls.client = cls.os.ec2api_client

    @attr(type='smoke')
    def test_create_authorize_security_group(self):
        # EC2 Create, authorize/revoke security group
        group_name = rand_name("securty_group-")
        group_description = group_name + " security group description "
        group = self.client.create_security_group(group_name,
                                                  group_description)
        self.addResourceCleanUp(self.client.delete_security_group, group_name)
        groups_get = self.client.get_all_security_groups(
            groupnames=(group_name,))
        self.assertEqual(len(groups_get), 1)
        group_get = groups_get[0]
        self.assertEqual(group.name, group_get.name)
        self.assertEqual(group.name, group_get.name)
        # ping (icmp_echo) and other icmp allowed from everywhere
        # from_port and to_port act as icmp type
        success = self.client.authorize_security_group(group_name,
                                                       ip_protocol="icmp",
                                                       cidr_ip="0.0.0.0/0",
                                                       from_port=-1,
                                                       to_port=-1)
        self.assertTrue(success)
        # allow standard ssh port from anywhere
        success = self.client.authorize_security_group(group_name,
                                                       ip_protocol="tcp",
                                                       cidr_ip="0.0.0.0/0",
                                                       from_port=22,
                                                       to_port=22)
        self.assertTrue(success)
        # TODO(afazekas): Duplicate tests
        group_get = self.client.get_all_security_groups(
            groupnames=(group_name,))[0]
        # remove listed rules
        for ip_permission in group_get.rules:
            for cidr in ip_permission.grants:
                self.assertTrue(self.client.revoke_security_group(group_name,
                                ip_protocol=ip_permission.ip_protocol,
                                cidr_ip=cidr,
                                from_port=ip_permission.from_port,
                                to_port=ip_permission.to_port))

        group_get = self.client.get_all_security_groups(
            groupnames=(group_name,))[0]
        # all rules shuld be removed now
        self.assertEqual(0, len(group_get.rules))
