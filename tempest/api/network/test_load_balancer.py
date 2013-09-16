# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack, LLC
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
from tempest.test import attr


class LoadBalancerJSON(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        create vIP, and Pool
        show vIP
        list vIP
        update vIP
        delete vIP
        update pool
        delete pool
    """

    @classmethod
    def setUpClass(cls):
        super(LoadBalancerJSON, cls).setUpClass()
        cls.network = cls.create_network()
        cls.name = cls.network['name']
        cls.subnet = cls.create_subnet(cls.network)
        pool_name = rand_name('pool-')
        vip_name = rand_name('vip-')
        cls.pool = cls.create_pool(pool_name, "ROUND_ROBIN",
                                   "HTTP", cls.subnet)
        cls.vip = cls.create_vip(vip_name, "HTTP", 80, cls.subnet, cls.pool)

    @attr(type='smoke')
    def test_list_vips(self):
        # Verify the vIP exists in the list of all vIPs
        resp, body = self.client.list_vips()
        self.assertEqual('200', resp['status'])
        vips = body['vips']
        found = None
        for n in vips:
            if (n['id'] == self.vip['id']):
                found = n['id']
        msg = "vIPs list doesn't contain created vip"
        self.assertIsNotNone(found, msg)

    def test_create_update_delete_pool_vip(self):
        # Creates a vip
        name = rand_name('vip-')
        resp, body = self.client.create_pool(rand_name("pool-"),
                                             "ROUND_ROBIN", "HTTP",
                                             self.subnet['id'])
        pool = body['pool']
        resp, body = self.client.create_vip(name, "HTTP", 80,
                                            self.subnet['id'], pool['id'])
        self.assertEqual('201', resp['status'])
        vip = body['vip']
        vip_id = vip['id']
        # Verification of vip update
        new_name = "New_vip"
        resp, body = self.client.update_vip(vip_id, new_name)
        self.assertEqual('200', resp['status'])
        updated_vip = body['vip']
        self.assertEqual(updated_vip['name'], new_name)
        # Verification of vip delete
        resp, body = self.client.delete_vip(vip['id'])
        self.assertEqual('204', resp['status'])
        # Verification of pool update
        new_name = "New_pool"
        resp, body = self.client.update_pool(pool['id'], new_name)
        self.assertEqual('200', resp['status'])
        updated_pool = body['pool']
        self.assertEqual(updated_pool['name'], new_name)
        # Verification of pool delete
        resp, body = self.client.delete_pool(pool['id'])
        self.assertEqual('204', resp['status'])

    @attr(type='smoke')
    def test_show_vip(self):
        # Verifies the details of a vip
        resp, body = self.client.show_vip(self.vip['id'])
        self.assertEqual('200', resp['status'])
        vip = body['vip']
        self.assertEqual(self.vip['id'], vip['id'])
        self.assertEqual(self.vip['name'], vip['name'])


class LoadBalancerXML(LoadBalancerJSON):
    _interface = 'xml'
