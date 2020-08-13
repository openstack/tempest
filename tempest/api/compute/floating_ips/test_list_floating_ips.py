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

from tempest.api.compute.floating_ips import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class FloatingIPDetailsTestJSON(base.BaseFloatingIPsTest):
    """Test floating ip details with compute microversion less than 2.36"""

    max_microversion = '2.35'

    @classmethod
    def resource_setup(cls):
        super(FloatingIPDetailsTestJSON, cls).resource_setup()
        cls.floating_ip = []
        for _ in range(3):
            body = cls.client.create_floating_ip(
                pool=CONF.network.floating_network_name)['floating_ip']
            cls.addClassResourceCleanup(cls.client.delete_floating_ip,
                                        body['id'])
            cls.floating_ip.append(body)

    @decorators.idempotent_id('16db31c3-fb85-40c9-bbe2-8cf7b67ff99f')
    def test_list_floating_ips(self):
        """Test listing floating ips"""
        body = self.client.list_floating_ips()['floating_ips']
        floating_ips = body
        self.assertNotEmpty(floating_ips,
                            "Expected floating IPs. Got zero.")
        for i in range(3):
            self.assertIn(self.floating_ip[i], floating_ips)

    @decorators.idempotent_id('eef497e0-8ff7-43c8-85ef-558440574f84')
    def test_get_floating_ip_details(self):
        """Test getting floating ip details"""
        # Creating a floating IP for which details are to be checked
        body = self.client.create_floating_ip(
            pool=CONF.network.floating_network_name)['floating_ip']
        floating_ip_id = body['id']
        self.addCleanup(self.client.delete_floating_ip,
                        floating_ip_id)
        floating_ip_instance_id = body['instance_id']
        floating_ip_ip = body['ip']
        floating_ip_fixed_ip = body['fixed_ip']
        body = self.client.show_floating_ip(floating_ip_id)['floating_ip']
        # Comparing the details of floating IP
        self.assertEqual(floating_ip_instance_id,
                         body['instance_id'])
        self.assertEqual(floating_ip_ip, body['ip'])
        self.assertEqual(floating_ip_fixed_ip,
                         body['fixed_ip'])
        self.assertEqual(floating_ip_id, body['id'])

    @decorators.idempotent_id('df389fc8-56f5-43cc-b290-20eda39854d3')
    def test_list_floating_ip_pools(self):
        """Test listing floating ip pools"""
        floating_ip_pools = self.pools_client.list_floating_ip_pools()
        self.assertNotEmpty(floating_ip_pools['floating_ip_pools'],
                            "Expected floating IP Pools. Got zero.")
