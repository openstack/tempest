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

from tempest.api.compute import base
from tempest.test import attr


class FloatingIPDetailsTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(FloatingIPDetailsTestJSON, cls).setUpClass()
        cls.client = cls.floating_ips_client
        cls.floating_ip = []
        cls.floating_ip_id = []
        for i in range(3):
            resp, body = cls.client.create_floating_ip()
            cls.floating_ip.append(body)
            cls.floating_ip_id.append(body['id'])

    @classmethod
    def tearDownClass(cls):
        for i in range(3):
            cls.client.delete_floating_ip(cls.floating_ip_id[i])
        super(FloatingIPDetailsTestJSON, cls).tearDownClass()

    @attr(type='gate')
    def test_list_floating_ips(self):
        # Positive test:Should return the list of floating IPs
        resp, body = self.client.list_floating_ips()
        self.assertEqual(200, resp.status)
        floating_ips = body
        self.assertNotEqual(0, len(floating_ips),
                            "Expected floating IPs. Got zero.")
        for i in range(3):
            self.assertIn(self.floating_ip[i], floating_ips)

    @attr(type='gate')
    def test_get_floating_ip_details(self):
        # Positive test:Should be able to GET the details of floatingIP
        # Creating a floating IP for which details are to be checked
        resp, body = self.client.create_floating_ip()
        floating_ip_id = body['id']
        self.addCleanup(self.client.delete_floating_ip,
                        floating_ip_id)
        floating_ip_instance_id = body['instance_id']
        floating_ip_ip = body['ip']
        floating_ip_fixed_ip = body['fixed_ip']
        resp, body = \
            self.client.get_floating_ip_details(floating_ip_id)
        self.assertEqual(200, resp.status)
        # Comparing the details of floating IP
        self.assertEqual(floating_ip_instance_id,
                         body['instance_id'])
        self.assertEqual(floating_ip_ip, body['ip'])
        self.assertEqual(floating_ip_fixed_ip,
                         body['fixed_ip'])
        self.assertEqual(floating_ip_id, body['id'])

    @attr(type='gate')
    def test_list_floating_ip_pools(self):
        # Positive test:Should return the list of floating IP Pools
        resp, floating_ip_pools = self.client.list_floating_ip_pools()
        self.assertEqual(200, resp.status)
        self.assertNotEqual(0, len(floating_ip_pools),
                            "Expected floating IP Pools. Got zero.")


class FloatingIPDetailsTestXML(FloatingIPDetailsTestJSON):
    _interface = 'xml'
