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

from tempest.api.compute import base
from tempest import test


class FloatingIPDetailsTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(FloatingIPDetailsTestJSON, cls).setup_clients()
        cls.client = cls.floating_ips_client

    @classmethod
    def resource_setup(cls):
        super(FloatingIPDetailsTestJSON, cls).resource_setup()
        cls.floating_ip = []
        cls.floating_ip_id = []
        for i in range(3):
            body = cls.client.create_floating_ip()
            cls.floating_ip.append(body)
            cls.floating_ip_id.append(body['id'])

    @classmethod
    def resource_cleanup(cls):
        for i in range(3):
            cls.client.delete_floating_ip(cls.floating_ip_id[i])
        super(FloatingIPDetailsTestJSON, cls).resource_cleanup()

    @test.attr(type='gate')
    @test.idempotent_id('16db31c3-fb85-40c9-bbe2-8cf7b67ff99f')
    @test.services('network')
    def test_list_floating_ips(self):
        # Positive test:Should return the list of floating IPs
        body = self.client.list_floating_ips()
        floating_ips = body
        self.assertNotEqual(0, len(floating_ips),
                            "Expected floating IPs. Got zero.")
        for i in range(3):
            self.assertIn(self.floating_ip[i], floating_ips)

    @test.attr(type='gate')
    @test.idempotent_id('eef497e0-8ff7-43c8-85ef-558440574f84')
    @test.services('network')
    def test_get_floating_ip_details(self):
        # Positive test:Should be able to GET the details of floatingIP
        # Creating a floating IP for which details are to be checked
        body = self.client.create_floating_ip()
        floating_ip_id = body['id']
        self.addCleanup(self.client.delete_floating_ip,
                        floating_ip_id)
        floating_ip_instance_id = body['instance_id']
        floating_ip_ip = body['ip']
        floating_ip_fixed_ip = body['fixed_ip']
        body = self.client.get_floating_ip_details(floating_ip_id)
        # Comparing the details of floating IP
        self.assertEqual(floating_ip_instance_id,
                         body['instance_id'])
        self.assertEqual(floating_ip_ip, body['ip'])
        self.assertEqual(floating_ip_fixed_ip,
                         body['fixed_ip'])
        self.assertEqual(floating_ip_id, body['id'])

    @test.attr(type='gate')
    @test.idempotent_id('df389fc8-56f5-43cc-b290-20eda39854d3')
    @test.services('network')
    def test_list_floating_ip_pools(self):
        # Positive test:Should return the list of floating IP Pools
        floating_ip_pools = self.client.list_floating_ip_pools()
        self.assertNotEqual(0, len(floating_ip_pools),
                            "Expected floating IP Pools. Got zero.")
