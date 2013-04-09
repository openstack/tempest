# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from tempest.common.utils.data_utils import rand_name
import tempest.tests.network.common as net_common


class TestNetworkBasicOps(net_common.TestNetworkSmokeCommon):

    """
    This smoke test suite assumes that Nova has been configured to
    boot VM's with Quantum-managed networking, and attempts to
    verify network connectivity as follows:

     * For a freshly-booted VM with an IP address ("port") on a given network:

       - the Tempest host can ping the IP address.  This implies that
         the VM has been assigned the correct IP address and has
         connectivity to the Tempest host.

       #TODO(mnewby) - Need to implement the following:
       - the Tempest host can ssh into the VM via the IP address and
         successfully execute the following:

         - ping an external IP address, implying external connectivity.

         - ping an external hostname, implying that dns is correctly
           configured.

         - ping an internal IP address, implying connectivity to another
           VM on the same network.

     There are presumed to be two types of networks: tenant and
     public.  A tenant network may or may not be reachable from the
     Tempest host.  A public network is assumed to be reachable from
     the Tempest host, and it should be possible to associate a public
     ('floating') IP address with a tenant ('fixed') IP address to
     faciliate external connectivity to a potentially unroutable
     tenant IP address.

     This test suite can be configured to test network connectivity to
     a VM via a tenant network, a public network, or both.  If both
     networking types are to be evaluated, tests that need to be
     executed remotely on the VM (via ssh) will only be run against
     one of the networks (to minimize test execution time).

     Determine which types of networks to test as follows:

     * Configure tenant network checks (via the
       'tenant_networks_reachable' key) if the Tempest host should
       have direct connectivity to tenant networks.  This is likely to
       be the case if Tempest is running on the same host as a
       single-node devstack installation with IP namespaces disabled.

     * Configure checks for a public network if a public network has
       been configured prior to the test suite being run and if the
       Tempest host should have connectivity to that public network.
       Checking connectivity for a public network requires that a
       value be provided for 'public_network_id'.  A value can
       optionally be provided for 'public_router_id' if tenants will
       use a shared router to access a public network (as is likely to
       be the case when IP namespaces are not enabled).  If a value is
       not provided for 'public_router_id', a router will be created
       for each tenant and use the network identified by
       'public_network_id' as its gateway.

    """

    @classmethod
    def check_preconditions(cls):
        super(TestNetworkBasicOps, cls).check_preconditions()
        cfg = cls.config.network
        if not (cfg.tenant_networks_reachable or cfg.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicOps, cls).setUpClass()
        cls.check_preconditions()
        cls.tenant_id = cls.manager._get_identity_client(
            cls.config.identity.username,
            cls.config.identity.password,
            cls.config.identity.tenant_name).tenant_id
        # TODO(mnewby) Consider looking up entities as needed instead
        # of storing them as collections on the class.
        cls.keypairs = {}
        cls.security_groups = {}
        cls.networks = []
        cls.subnets = []
        cls.routers = []
        cls.servers = []
        cls.floating_ips = {}

    def _get_router(self, tenant_id):
        """Retrieve a router for the given tenant id.

        If a public router has been configured, it will be returned.

        If a public router has not been configured, but a public
        network has, a tenant router will be created and returned that
        routes traffic to the public network.

        """
        router_id = self.config.network.public_router_id
        network_id = self.config.network.public_network_id
        if router_id:
            result = self.network_client.show_router(router_id)
            return net_common.AttributeDict(**result['router'])
        elif network_id:
            router = self._create_router(tenant_id)
            router.add_gateway(network_id)
            return router
        else:
            raise Exception("Neither of 'public_router_id' or "
                            "'public_network_id' has been defined.")

    def _create_router(self, tenant_id, namestart='router-smoke-'):
        name = rand_name(namestart)
        body = dict(
            router=dict(
                name=name,
                admin_state_up=True,
                tenant_id=tenant_id,
            ),
        )
        result = self.network_client.create_router(body=body)
        router = net_common.DeletableRouter(client=self.network_client,
                                            **result['router'])
        self.assertEqual(router.name, name)
        self.set_resource(name, router)
        return router

    def test_001_create_keypairs(self):
        self.keypairs[self.tenant_id] = self._create_keypair(
            self.compute_client)

    def test_002_create_security_groups(self):
        self.security_groups[self.tenant_id] = self._create_security_group(
            self.compute_client)

    def test_003_create_networks(self):
        network = self._create_network(self.tenant_id)
        router = self._get_router(self.tenant_id)
        subnet = self._create_subnet(network)
        subnet.add_to_router(router.id)
        self.networks.append(network)
        self.subnets.append(subnet)
        self.routers.append(router)

    def test_004_check_networks(self):
        #Checks that we see the newly created network/subnet/router via
        #checking the result of list_[networks,routers,subnets]
        seen_nets = self._list_networks()
        seen_names = [n['name'] for n in seen_nets]
        seen_ids = [n['id'] for n in seen_nets]
        for mynet in self.networks:
            self.assertIn(mynet.name, seen_names)
            self.assertIn(mynet.id, seen_ids)
        seen_subnets = self._list_subnets()
        seen_net_ids = [n['network_id'] for n in seen_subnets]
        seen_subnet_ids = [n['id'] for n in seen_subnets]
        for mynet in self.networks:
            self.assertIn(mynet.id, seen_net_ids)
        for mysubnet in self.subnets:
            self.assertIn(mysubnet.id, seen_subnet_ids)
        seen_routers = self._list_routers()
        seen_router_ids = [n['id'] for n in seen_routers]
        seen_router_names = [n['name'] for n in seen_routers]
        for myrouter in self.routers:
            self.assertIn(myrouter.name, seen_router_names)
            self.assertIn(myrouter.id, seen_router_ids)

    def test_005_create_servers(self):
        if not (self.keypairs or self.security_groups or self.networks):
            raise self.skipTest('Necessary resources have not been defined')
        for i, network in enumerate(self.networks):
            tenant_id = network.tenant_id
            name = rand_name('server-smoke-%d-' % i)
            keypair_name = self.keypairs[tenant_id].name
            security_groups = [self.security_groups[tenant_id].name]
            server = self._create_server(self.compute_client, network,
                                         name, keypair_name, security_groups)
            self.servers.append(server)

    def test_006_check_tenant_network_connectivity(self):
        if not self.config.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            raise self.skipTest(msg)
        if not self.servers:
            raise self.skipTest("No VM's have been created")
        for server in self.servers:
            for net_name, ip_addresses in server.networks.iteritems():
                for ip_address in ip_addresses:
                    self.assertTrue(self._ping_ip_address(ip_address),
                                    "Timed out waiting for %s's ip to become "
                                    "reachable" % server.name)

    def test_007_assign_floating_ips(self):
        public_network_id = self.config.network.public_network_id
        if not public_network_id:
            raise self.skipTest('Public network not configured')
        if not self.servers:
            raise self.skipTest("No VM's have been created")
        for server in self.servers:
            floating_ip = self._create_floating_ip(server, public_network_id)
            self.floating_ips.setdefault(server, [])
            self.floating_ips[server].append(floating_ip)

    def test_008_check_public_network_connectivity(self):
        if not self.floating_ips:
            raise self.skipTest('No floating ips have been allocated.')
        for server, floating_ips in self.floating_ips.iteritems():
            for floating_ip in floating_ips:
                ip_address = floating_ip.floating_ip_address
                self.assertTrue(self._ping_ip_address(ip_address),
                                "Timed out waiting for %s's ip to become "
                                "reachable" % server.name)
