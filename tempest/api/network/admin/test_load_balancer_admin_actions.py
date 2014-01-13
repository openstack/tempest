# Copyright 2014 Mirantis.inc
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


class LoadBalancerAdminTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    """
    Test admin actions for load balancer.

    Create VIP for another tenant
    Create health monitor for another tenant
    """

    @classmethod
    def setUpClass(cls):
        super(LoadBalancerAdminTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        cls.force_tenant_isolation = True
        manager = cls.get_client_manager()
        cls.client = manager.network_client
        username, tenant_name, passwd = cls.isolated_creds.get_primary_creds()
        cls.tenant_id = cls.os_adm.identity_client.get_tenant_by_name(
            tenant_name)['id']
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.pool = cls.create_pool(data_utils.rand_name('pool-'),
                                   "ROUND_ROBIN", "HTTP", cls.subnet)

    @test.attr(type='smoke')
    def test_create_vip_as_admin_for_another_tenant(self):
        name = data_utils.rand_name('vip-')
        resp, body = self.admin_client.create_pool(
            name=data_utils.rand_name('pool-'), lb_method="ROUND_ROBIN",
            protocol="HTTP", subnet_id=self.subnet['id'],
            tenant_id=self.tenant_id)
        self.assertEqual('201', resp['status'])
        pool = body['pool']
        self.addCleanup(self.admin_client.delete_pool, pool['id'])
        resp, body = self.admin_client.create_vip(name=name,
                                                  protocol="HTTP",
                                                  protocol_port=80,
                                                  subnet_id=self.subnet['id'],
                                                  pool_id=pool['id'],
                                                  tenant_id=self.tenant_id)
        self.assertEqual('201', resp['status'])
        vip = body['vip']
        self.addCleanup(self.admin_client.delete_vip, vip['id'])
        self.assertIsNotNone(vip['id'])
        self.assertEqual(self.tenant_id, vip['tenant_id'])
        resp, body = self.client.show_vip(vip['id'])
        self.assertEqual('200', resp['status'])
        show_vip = body['vip']
        self.assertEqual(vip['id'], show_vip['id'])
        self.assertEqual(vip['name'], show_vip['name'])

    @test.attr(type='smoke')
    def test_create_health_monitor_as_admin_for_another_tenant(self):
        resp, body = (
            self.admin_client.create_health_monitor(delay=4,
                                                    max_retries=3,
                                                    type="TCP",
                                                    timeout=1,
                                                    tenant_id=self.tenant_id))
        self.assertEqual('201', resp['status'])
        health_monitor = body['health_monitor']
        self.addCleanup(self.admin_client.delete_health_monitor,
                        health_monitor['id'])
        self.assertIsNotNone(health_monitor['id'])
        self.assertEqual(self.tenant_id, health_monitor['tenant_id'])
        resp, body = self.client.show_health_monitor(health_monitor['id'])
        self.assertEqual('200', resp['status'])
        show_health_monitor = body['health_monitor']
        self.assertEqual(health_monitor['id'], show_health_monitor['id'])

    @test.attr(type='smoke')
    def test_create_pool_from_admin_user_other_tenant(self):
        resp, body = self.admin_client.create_pool(
            name=data_utils.rand_name('pool-'), lb_method="ROUND_ROBIN",
            protocol="HTTP", subnet_id=self.subnet['id'],
            tenant_id=self.tenant_id)
        self.assertEqual('201', resp['status'])
        pool = body['pool']
        self.addCleanup(self.admin_client.delete_pool, pool['id'])
        self.assertIsNotNone(pool['id'])
        self.assertEqual(self.tenant_id, pool['tenant_id'])

    @test.attr(type='smoke')
    def test_create_member_from_admin_user_other_tenant(self):
        resp, body = self.admin_client.create_member(
            address="10.0.9.47", protocol_port=80, pool_id=self.pool['id'],
            tenant_id=self.tenant_id)
        self.assertEqual('201', resp['status'])
        member = body['member']
        self.addCleanup(self.admin_client.delete_member, member['id'])
        self.assertIsNotNone(member['id'])
        self.assertEqual(self.tenant_id, member['tenant_id'])


class LoadBalancerAdminTestXML(LoadBalancerAdminTestJSON):
    _interface = 'xml'
