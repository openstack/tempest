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

import testtools

from tempest.api.network import base
from tempest.common import identity
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class RoutersAdminTest(base.BaseAdminNetworkTest):
    # NOTE(salv-orlando): This class inherits from BaseAdminNetworkTest
    # as some router operations, such as enabling or disabling SNAT
    # require admin credentials by default

    def _cleanup_router(self, router):
        self.delete_router(router)

    def _create_router(self, name=None, admin_state_up=False,
                       external_network_id=None, enable_snat=None):
        # associate a cleanup with created routers to avoid quota limits
        router = self.create_router(name, admin_state_up,
                                    external_network_id, enable_snat)
        self.addCleanup(self._cleanup_router, router)
        return router

    @classmethod
    def skip_checks(cls):
        super(RoutersAdminTest, cls).skip_checks()
        if not utils.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)

    @decorators.idempotent_id('e54dd3a3-4352-4921-b09d-44369ae17397')
    def test_create_router_setting_project_id(self):
        # Test creating router from admin user setting project_id.
        project = data_utils.rand_name('test_tenant_')
        description = data_utils.rand_name('desc_')
        project = identity.identity_utils(self.os_admin).create_project(
            name=project, description=description)
        project_id = project['id']
        self.addCleanup(identity.identity_utils(self.os_admin).delete_project,
                        project_id)

        name = data_utils.rand_name('router-')
        create_body = self.admin_routers_client.create_router(
            name=name, tenant_id=project_id)
        self.addCleanup(self.admin_routers_client.delete_router,
                        create_body['router']['id'])
        self.assertEqual(project_id, create_body['router']['tenant_id'])

    @decorators.idempotent_id('847257cc-6afd-4154-b8fb-af49f5670ce8')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_create_router_with_default_snat_value(self):
        # Create a router with default snat rule
        router = self._create_router(
            external_network_id=CONF.network.public_network_id)
        self._verify_router_gateway(
            router['id'], {'network_id': CONF.network.public_network_id,
                           'enable_snat': True})

    @decorators.idempotent_id('ea74068d-09e9-4fd7-8995-9b6a1ace920f')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_create_router_with_snat_explicit(self):
        name = data_utils.rand_name('snat-router')
        # Create a router enabling snat attributes
        enable_snat_states = [False, True]
        for enable_snat in enable_snat_states:
            external_gateway_info = {
                'network_id': CONF.network.public_network_id,
                'enable_snat': enable_snat}
            create_body = self.admin_routers_client.create_router(
                name=name, external_gateway_info=external_gateway_info)
            self.addCleanup(self.admin_routers_client.delete_router,
                            create_body['router']['id'])
            # Verify snat attributes after router creation
            self._verify_router_gateway(create_body['router']['id'],
                                        exp_ext_gw_info=external_gateway_info)

    def _verify_router_gateway(self, router_id, exp_ext_gw_info=None):
        show_body = self.admin_routers_client.show_router(router_id)
        actual_ext_gw_info = show_body['router']['external_gateway_info']
        if exp_ext_gw_info is None:
            self.assertIsNone(actual_ext_gw_info)
            return
        # Verify only keys passed in exp_ext_gw_info
        for k, v in exp_ext_gw_info.items():
            self.assertEqual(v, actual_ext_gw_info[k])

    def _verify_gateway_port(self, router_id):
        list_body = self.admin_ports_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router_id)
        self.assertEqual(len(list_body['ports']), 1)
        gw_port = list_body['ports'][0]
        fixed_ips = gw_port['fixed_ips']
        self.assertNotEmpty(fixed_ips)
        # Assert that all of the IPs from the router gateway port
        # are allocated from a valid public subnet.
        public_net_body = self.admin_networks_client.show_network(
            CONF.network.public_network_id)
        public_subnet_ids = public_net_body['network']['subnets']
        for fixed_ip in fixed_ips:
            subnet_id = fixed_ip['subnet_id']
            self.assertIn(subnet_id, public_subnet_ids)

    @decorators.idempotent_id('6cc285d8-46bf-4f36-9b1a-783e3008ba79')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_update_router_set_gateway(self):
        router = self._create_router()
        self.routers_client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id})
        # Verify operation - router
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id})
        self._verify_gateway_port(router['id'])

    @decorators.idempotent_id('b386c111-3b21-466d-880c-5e72b01e1a33')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_update_router_set_gateway_with_snat_explicit(self):
        router = self._create_router()
        self.admin_routers_client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': True})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': True})
        self._verify_gateway_port(router['id'])

    @decorators.idempotent_id('96536bc7-8262-4fb2-9967-5c46940fa279')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_update_router_set_gateway_without_snat(self):
        router = self._create_router()
        self.admin_routers_client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': False})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': False})
        self._verify_gateway_port(router['id'])

    @decorators.idempotent_id('ad81b7ee-4f81-407b-a19c-17e623f763e8')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_update_router_unset_gateway(self):
        router = self._create_router(
            external_network_id=CONF.network.public_network_id)
        self.routers_client.update_router(router['id'],
                                          external_gateway_info={})
        self._verify_router_gateway(router['id'])
        # No gateway port expected
        list_body = self.admin_ports_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router['id'])
        self.assertFalse(list_body['ports'])

    @decorators.idempotent_id('f2faf994-97f4-410b-a831-9bc977b64374')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_update_router_reset_gateway_without_snat(self):
        router = self._create_router(
            external_network_id=CONF.network.public_network_id)
        self.admin_routers_client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': False})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': False})
        self._verify_gateway_port(router['id'])


class RoutersIpV6AdminTest(RoutersAdminTest):
    _ip_version = 6
