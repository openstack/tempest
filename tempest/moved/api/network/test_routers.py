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

import netaddr
import six

from tempest.api.network import base_routers as base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class RoutersTest(base.BaseRouterTest):

    @classmethod
    def skip_checks(cls):
        super(RoutersTest, cls).skip_checks()
        if not test.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(RoutersTest, cls).setup_clients()
        cls.identity_admin_client = cls.os_adm.identity_client

    @classmethod
    def resource_setup(cls):
        super(RoutersTest, cls).resource_setup()
        cls.tenant_cidr = (CONF.network.project_network_cidr
                           if cls._ip_version == 4 else
                           CONF.network.project_network_v6_cidr)

    @test.attr(type='smoke')
    @test.idempotent_id('f64403e2-8483-4b34-8ccd-b09a87bcc68c')
    def test_create_show_list_update_delete_router(self):
        # Create a router
        # NOTE(salv-orlando): Do not invoke self.create_router
        # as we need to check the response code
        name = data_utils.rand_name('router-')
        create_body = self.routers_client.create_router(
            name=name, external_gateway_info={
                "network_id": CONF.network.public_network_id},
            admin_state_up=False)
        self.addCleanup(self._delete_router, create_body['router']['id'])
        self.assertEqual(create_body['router']['name'], name)
        self.assertEqual(
            create_body['router']['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        self.assertEqual(create_body['router']['admin_state_up'], False)
        # Show details of the created router
        show_body = self.routers_client.show_router(
            create_body['router']['id'])
        self.assertEqual(show_body['router']['name'], name)
        self.assertEqual(
            show_body['router']['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        self.assertEqual(show_body['router']['admin_state_up'], False)
        # List routers and verify if created router is there in response
        list_body = self.routers_client.list_routers()
        routers_list = list()
        for router in list_body['routers']:
            routers_list.append(router['id'])
        self.assertIn(create_body['router']['id'], routers_list)
        # Update the name of router and verify if it is updated
        updated_name = 'updated ' + name
        update_body = self.routers_client.update_router(
            create_body['router']['id'], name=updated_name)
        self.assertEqual(update_body['router']['name'], updated_name)
        show_body = self.routers_client.show_router(
            create_body['router']['id'])
        self.assertEqual(show_body['router']['name'], updated_name)

    @test.idempotent_id('e54dd3a3-4352-4921-b09d-44369ae17397')
    def test_create_router_setting_project_id(self):
        # Test creating router from admin user setting project_id.
        project = data_utils.rand_name('test_tenant_')
        description = data_utils.rand_name('desc_')
        project = self.identity_utils.create_project(name=project,
                                                     description=description)
        project_id = project['id']
        self.addCleanup(self.identity_utils.delete_project, project_id)

        name = data_utils.rand_name('router-')
        create_body = self.admin_routers_client.create_router(
            name=name, tenant_id=project_id)
        self.addCleanup(self.admin_routers_client.delete_router,
                        create_body['router']['id'])
        self.assertEqual(project_id, create_body['router']['tenant_id'])

    @test.idempotent_id('847257cc-6afd-4154-b8fb-af49f5670ce8')
    @test.requires_ext(extension='ext-gw-mode', service='network')
    def test_create_router_with_default_snat_value(self):
        # Create a router with default snat rule
        name = data_utils.rand_name('router')
        router = self._create_router(
            name, external_network_id=CONF.network.public_network_id)
        self._verify_router_gateway(
            router['id'], {'network_id': CONF.network.public_network_id,
                           'enable_snat': True})

    @test.idempotent_id('ea74068d-09e9-4fd7-8995-9b6a1ace920f')
    @test.requires_ext(extension='ext-gw-mode', service='network')
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

    @test.attr(type='smoke')
    @test.idempotent_id('b42e6e39-2e37-49cc-a6f4-8467e940900a')
    def test_add_remove_router_interface_with_subnet_id(self):
        network = self.create_network()
        subnet = self.create_subnet(network)
        router = self._create_router(data_utils.rand_name('router-'))
        # Add router interface with subnet id
        interface = self.routers_client.add_router_interface(
            router['id'], subnet_id=subnet['id'])
        self.addCleanup(self._remove_router_interface_with_subnet_id,
                        router['id'], subnet['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        show_port_body = self.ports_client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('2b7d2f37-6748-4d78-92e5-1d590234f0d5')
    def test_add_remove_router_interface_with_port_id(self):
        network = self.create_network()
        self.create_subnet(network)
        router = self._create_router(data_utils.rand_name('router-'))
        port_body = self.ports_client.create_port(
            network_id=network['id'])
        # add router interface to port created above
        interface = self.routers_client.add_router_interface(
            router['id'],
            port_id=port_body['port']['id'])
        self.addCleanup(self._remove_router_interface_with_port_id,
                        router['id'], port_body['port']['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        show_port_body = self.ports_client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    def _verify_router_gateway(self, router_id, exp_ext_gw_info=None):
        show_body = self.admin_routers_client.show_router(router_id)
        actual_ext_gw_info = show_body['router']['external_gateway_info']
        if exp_ext_gw_info is None:
            self.assertIsNone(actual_ext_gw_info)
            return
        # Verify only keys passed in exp_ext_gw_info
        for k, v in six.iteritems(exp_ext_gw_info):
            self.assertEqual(v, actual_ext_gw_info[k])

    def _verify_gateway_port(self, router_id):
        list_body = self.admin_ports_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router_id)
        self.assertEqual(len(list_body['ports']), 1)
        gw_port = list_body['ports'][0]
        fixed_ips = gw_port['fixed_ips']
        self.assertGreaterEqual(len(fixed_ips), 1)
        public_net_body = self.admin_networks_client.show_network(
            CONF.network.public_network_id)
        public_subnet_id = public_net_body['network']['subnets'][0]
        self.assertIn(public_subnet_id,
                      map(lambda x: x['subnet_id'], fixed_ips))

    @test.idempotent_id('6cc285d8-46bf-4f36-9b1a-783e3008ba79')
    def test_update_router_set_gateway(self):
        router = self._create_router(data_utils.rand_name('router-'))
        self.routers_client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id})
        # Verify operation - router
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id})
        self._verify_gateway_port(router['id'])

    @test.idempotent_id('b386c111-3b21-466d-880c-5e72b01e1a33')
    @test.requires_ext(extension='ext-gw-mode', service='network')
    def test_update_router_set_gateway_with_snat_explicit(self):
        router = self._create_router(data_utils.rand_name('router-'))
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

    @test.idempotent_id('96536bc7-8262-4fb2-9967-5c46940fa279')
    @test.requires_ext(extension='ext-gw-mode', service='network')
    def test_update_router_set_gateway_without_snat(self):
        router = self._create_router(data_utils.rand_name('router-'))
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

    @test.idempotent_id('ad81b7ee-4f81-407b-a19c-17e623f763e8')
    def test_update_router_unset_gateway(self):
        router = self._create_router(
            data_utils.rand_name('router-'),
            external_network_id=CONF.network.public_network_id)
        self.routers_client.update_router(router['id'],
                                          external_gateway_info={})
        self._verify_router_gateway(router['id'])
        # No gateway port expected
        list_body = self.admin_ports_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router['id'])
        self.assertFalse(list_body['ports'])

    @test.idempotent_id('f2faf994-97f4-410b-a831-9bc977b64374')
    @test.requires_ext(extension='ext-gw-mode', service='network')
    def test_update_router_reset_gateway_without_snat(self):
        router = self._create_router(
            data_utils.rand_name('router-'),
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

    @test.idempotent_id('c86ac3a8-50bd-4b00-a6b8-62af84a0765c')
    @test.requires_ext(extension='extraroute', service='network')
    def test_update_delete_extra_route(self):
        # Create different cidr for each subnet to avoid cidr duplicate
        # The cidr starts from project_cidr
        next_cidr = netaddr.IPNetwork(self.tenant_cidr)
        # Prepare to build several routes
        test_routes = []
        routes_num = 4
        # Create a router
        router = self._create_router(
            data_utils.rand_name('router-'), True)
        self.addCleanup(
            self._delete_extra_routes,
            router['id'])
        # Update router extra route, second ip of the range is
        # used as next hop
        for i in range(routes_num):
            network = self.create_network()
            subnet = self.create_subnet(network, cidr=next_cidr)
            next_cidr = next_cidr.next()

            # Add router interface with subnet id
            self.create_router_interface(router['id'], subnet['id'])

            cidr = netaddr.IPNetwork(subnet['cidr'])
            next_hop = str(cidr[2])
            destination = str(subnet['cidr'])
            test_routes.append(
                {'nexthop': next_hop, 'destination': destination}
            )

        test_routes.sort(key=lambda x: x['destination'])
        extra_route = self.routers_client.update_router(
            router['id'], routes=test_routes)
        show_body = self.routers_client.show_router(router['id'])
        # Assert the number of routes
        self.assertEqual(routes_num, len(extra_route['router']['routes']))
        self.assertEqual(routes_num, len(show_body['router']['routes']))

        routes = extra_route['router']['routes']
        routes.sort(key=lambda x: x['destination'])
        # Assert the nexthops & destination
        for i in range(routes_num):
            self.assertEqual(test_routes[i]['destination'],
                             routes[i]['destination'])
            self.assertEqual(test_routes[i]['nexthop'], routes[i]['nexthop'])

        routes = show_body['router']['routes']
        routes.sort(key=lambda x: x['destination'])
        for i in range(routes_num):
            self.assertEqual(test_routes[i]['destination'],
                             routes[i]['destination'])
            self.assertEqual(test_routes[i]['nexthop'], routes[i]['nexthop'])

        self._delete_extra_routes(router['id'])
        show_body_after_deletion = self.routers_client.show_router(
            router['id'])
        self.assertEmpty(show_body_after_deletion['router']['routes'])

    def _delete_extra_routes(self, router_id):
        self.routers_client.update_router(router_id, routes=None)

    @test.idempotent_id('a8902683-c788-4246-95c7-ad9c6d63a4d9')
    def test_update_router_admin_state(self):
        router = self._create_router(data_utils.rand_name('router-'))
        self.assertFalse(router['admin_state_up'])
        # Update router admin state
        update_body = self.routers_client.update_router(router['id'],
                                                        admin_state_up=True)
        self.assertTrue(update_body['router']['admin_state_up'])
        show_body = self.routers_client.show_router(router['id'])
        self.assertTrue(show_body['router']['admin_state_up'])

    @test.attr(type='smoke')
    @test.idempotent_id('802c73c9-c937-4cef-824b-2191e24a6aab')
    def test_add_multiple_router_interfaces(self):
        network01 = self.create_network(
            network_name=data_utils.rand_name('router-network01-'))
        network02 = self.create_network(
            network_name=data_utils.rand_name('router-network02-'))
        subnet01 = self.create_subnet(network01)
        sub02_cidr = netaddr.IPNetwork(self.tenant_cidr).next()
        subnet02 = self.create_subnet(network02, cidr=sub02_cidr)
        router = self._create_router(data_utils.rand_name('router-'))
        interface01 = self._add_router_interface_with_subnet_id(router['id'],
                                                                subnet01['id'])
        self._verify_router_interface(router['id'], subnet01['id'],
                                      interface01['port_id'])
        interface02 = self._add_router_interface_with_subnet_id(router['id'],
                                                                subnet02['id'])
        self._verify_router_interface(router['id'], subnet02['id'],
                                      interface02['port_id'])

    @test.idempotent_id('96522edf-b4b5-45d9-8443-fa11c26e6eff')
    def test_router_interface_port_update_with_fixed_ip(self):
        network = self.create_network()
        subnet = self.create_subnet(network)
        router = self._create_router(data_utils.rand_name('router-'))
        fixed_ip = [{'subnet_id': subnet['id']}]
        interface = self._add_router_interface_with_subnet_id(router['id'],
                                                              subnet['id'])
        self.assertIn('port_id', interface)
        self.assertIn('subnet_id', interface)
        port = self.ports_client.show_port(interface['port_id'])
        self.assertEqual(port['port']['id'], interface['port_id'])
        router_port = self.ports_client.update_port(port['port']['id'],
                                                    fixed_ips=fixed_ip)
        self.assertEqual(subnet['id'],
                         router_port['port']['fixed_ips'][0]['subnet_id'])

    def _verify_router_interface(self, router_id, subnet_id, port_id):
        show_port_body = self.ports_client.show_port(port_id)
        interface_port = show_port_body['port']
        self.assertEqual(router_id, interface_port['device_id'])
        self.assertEqual(subnet_id,
                         interface_port['fixed_ips'][0]['subnet_id'])


class RoutersIpV6Test(RoutersTest):
    _ip_version = 6


class DvrRoutersTest(base.BaseRouterTest):

    @classmethod
    def skip_checks(cls):
        super(DvrRoutersTest, cls).skip_checks()
        if not test.is_extension_enabled('dvr', 'network'):
            msg = "DVR extension not enabled."
            raise cls.skipException(msg)

    @test.idempotent_id('141297aa-3424-455d-aa8d-f2d95731e00a')
    def test_create_distributed_router(self):
        name = data_utils.rand_name('router')
        create_body = self.admin_routers_client.create_router(
            name=name, distributed=True)
        self.addCleanup(self._delete_router,
                        create_body['router']['id'],
                        self.admin_routers_client)
        self.assertTrue(create_body['router']['distributed'])

    @test.idempotent_id('644d7a4a-01a1-4b68-bb8d-0c0042cb1729')
    def test_convert_centralized_router(self):
        router = self._create_router(data_utils.rand_name('router'))
        self.assertNotIn('distributed', router)
        update_body = self.admin_routers_client.update_router(router['id'],
                                                              distributed=True)
        self.assertTrue(update_body['router']['distributed'])
        show_body = self.admin_routers_client.show_router(router['id'])
        self.assertTrue(show_body['router']['distributed'])
        show_body = self.routers_client.show_router(router['id'])
        self.assertNotIn('distributed', show_body['router'])
