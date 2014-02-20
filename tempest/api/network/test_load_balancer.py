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
from tempest import test


class LoadBalancerTestJSON(base.BaseNetworkTest):
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
        show pool
        list pool
        health monitoring operations
    """

    @classmethod
    def setUpClass(cls):
        super(LoadBalancerTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        cls.network = cls.create_network()
        cls.name = cls.network['name']
        cls.subnet = cls.create_subnet(cls.network)
        pool_name = data_utils.rand_name('pool-')
        vip_name = data_utils.rand_name('vip-')
        cls.pool = cls.create_pool(pool_name, "ROUND_ROBIN",
                                   "HTTP", cls.subnet)
        cls.vip = cls.create_vip(name=vip_name,
                                 protocol="HTTP",
                                 protocol_port=80,
                                 subnet=cls.subnet,
                                 pool=cls.pool)
        cls.member = cls.create_member(80, cls.pool)
        cls.health_monitor = cls.create_health_monitor(delay=4,
                                                       max_retries=3,
                                                       Type="TCP",
                                                       timeout=1)

    @test.attr(type='smoke')
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
        name = data_utils.rand_name('vip-')
        resp, body = self.client.create_pool(
            name=data_utils.rand_name("pool-"),
            lb_method='ROUND_ROBIN',
            protocol='HTTP',
            subnet_id=self.subnet['id'])
        pool = body['pool']
        resp, body = self.client.create_vip(name=name,
                                            protocol="HTTP",
                                            protocol_port=80,
                                            subnet_id=self.subnet['id'],
                                            pool_id=pool['id'])
        self.assertEqual('201', resp['status'])
        vip = body['vip']
        vip_id = vip['id']
        # Verification of vip update
        new_name = "New_vip"
        resp, body = self.client.update_vip(vip_id, name=new_name)
        self.assertEqual('200', resp['status'])
        updated_vip = body['vip']
        self.assertEqual(updated_vip['name'], new_name)
        # Verification of vip delete
        resp, body = self.client.delete_vip(vip['id'])
        self.assertEqual('204', resp['status'])
        # Verification of pool update
        new_name = "New_pool"
        resp, body = self.client.update_pool(pool['id'],
                                             name=new_name)
        self.assertEqual('200', resp['status'])
        updated_pool = body['pool']
        self.assertEqual(updated_pool['name'], new_name)
        # Verification of pool delete
        resp, body = self.client.delete_pool(pool['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_show_vip(self):
        # Verifies the details of a vip
        resp, body = self.client.show_vip(self.vip['id'])
        self.assertEqual('200', resp['status'])
        vip = body['vip']
        self.assertEqual(self.vip['id'], vip['id'])
        self.assertEqual(self.vip['name'], vip['name'])

    @test.attr(type='smoke')
    def test_show_pool(self):
        # Verifies the details of a pool
        resp, body = self.client.show_pool(self.pool['id'])
        self.assertEqual('200', resp['status'])
        pool = body['pool']
        self.assertEqual(self.pool['id'], pool['id'])
        self.assertEqual(self.pool['name'], pool['name'])

    @test.attr(type='smoke')
    def test_list_pools(self):
        # Verify the pool exists in the list of all pools
        resp, body = self.client.list_pools()
        self.assertEqual('200', resp['status'])
        pools = body['pools']
        self.assertIn(self.pool['id'], [p['id'] for p in pools])

    @test.attr(type='smoke')
    def test_list_members(self):
        # Verify the member exists in the list of all members
        resp, body = self.client.list_members()
        self.assertEqual('200', resp['status'])
        members = body['members']
        self.assertIn(self.member['id'], [m['id'] for m in members])

    @test.attr(type='smoke')
    def test_create_update_delete_member(self):
        # Creates a member
        resp, body = self.client.create_member("10.0.9.47", 80,
                                               self.pool['id'])
        self.assertEqual('201', resp['status'])
        member = body['member']
        # Verification of member update
        resp, body = self.client.update_member(False, member['id'])
        self.assertEqual('200', resp['status'])
        updated_member = body['member']
        self.assertFalse(updated_member['admin_state_up'])
        # Verification of member delete
        resp, body = self.client.delete_member(member['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_show_member(self):
        # Verifies the details of a member
        resp, body = self.client.show_member(self.member['id'])
        self.assertEqual('200', resp['status'])
        member = body['member']
        self.assertEqual(self.member['id'], member['id'])
        self.assertEqual(self.member['admin_state_up'],
                         member['admin_state_up'])

    @test.attr(type='smoke')
    def test_list_health_monitors(self):
        # Verify the health monitor exists in the list of all health monitors
        resp, body = self.client.list_health_monitors()
        self.assertEqual('200', resp['status'])
        health_monitors = body['health_monitors']
        self.assertIn(self.health_monitor['id'],
                      [h['id'] for h in health_monitors])

    @test.attr(type='smoke')
    def test_create_update_delete_health_monitor(self):
        # Creates a health_monitor
        resp, body = self.client.create_health_monitor(delay=4,
                                                       max_retries=3,
                                                       type="TCP",
                                                       timeout=1)
        self.assertEqual('201', resp['status'])
        health_monitor = body['health_monitor']
        # Verification of health_monitor update
        resp, body = (self.client.update_health_monitor
                     (health_monitor['id'],
                      admin_state_up=False))
        self.assertEqual('200', resp['status'])
        updated_health_monitor = body['health_monitor']
        self.assertFalse(updated_health_monitor['admin_state_up'])
        # Verification of health_monitor delete
        resp, body = self.client.delete_health_monitor(health_monitor['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_show_health_monitor(self):
        # Verifies the details of a health_monitor
        resp, body = self.client.show_health_monitor(self.health_monitor['id'])
        self.assertEqual('200', resp['status'])
        health_monitor = body['health_monitor']
        self.assertEqual(self.health_monitor['id'], health_monitor['id'])
        self.assertEqual(self.health_monitor['admin_state_up'],
                         health_monitor['admin_state_up'])

    @test.attr(type='smoke')
    def test_associate_disassociate_health_monitor_with_pool(self):
        # Verify that a health monitor can be associated with a pool
        resp, body = (self.client.associate_health_monitor_with_pool
                     (self.health_monitor['id'], self.pool['id']))
        self.assertEqual('201', resp['status'])
        # Verify that a health monitor can be disassociated from a pool
        resp, body = (self.client.disassociate_health_monitor_with_pool
                     (self.health_monitor['id'], self.pool['id']))
        self.assertEqual('204', resp['status'])

    @test.attr(type='smoke')
    def test_get_lb_pool_stats(self):
        # Verify the details of pool stats
        resp, body = self.client.list_lb_pool_stats(self.pool['id'])
        self.assertEqual('200', resp['status'])
        stats = body['stats']
        self.assertIn("bytes_in", stats)
        self.assertIn("total_connections", stats)
        self.assertIn("active_connections", stats)
        self.assertIn("bytes_out", stats)


class LoadBalancerTestXML(LoadBalancerTestJSON):
    _interface = 'xml'
